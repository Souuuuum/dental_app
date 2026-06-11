from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db.models import Q, F
from .models import Patient
from collections import defaultdict
from datetime import datetime, date
from django.db.models import Sum
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
# ================== 🔐 LOGIN ==================
def login_view(request):

    error = ""

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user:
            login(request, user)
            return redirect('/')

        else:
            error = "اسم المستخدم أو كلمة السر خاطئة"

    return render(request, 'login.html', {
        'error': error
    })


# ================== 🚪 LOGOUT ==================
def logout_view(request):
    logout(request)
    return redirect('/login/')
# ================== 🏠 HOME ==================
@login_required
def home(request):
    today = date.today()
    today_patients = Patient.objects.filter(
        next_appointment=today,
        is_appointment=False )
    today_total = sum(p.paid_amount for p in today_patients)
    total=sum(p.total_amount for p in today_patients)
    t=total-today_total
    # POST → تعديل كامل
    if request.method == "POST":
        patient_id = request.POST.get("patient_id")
        p = Patient.objects.get(id=patient_id)

        p.first_name = request.POST.get("first_name")
        p.last_name = request.POST.get("last_name")
        p.treatment = request.POST.get("treatment")

        p.total_amount = float(request.POST.get("total_amount") or 0)
        p.paid_amount = float(request.POST.get("paid_amount") or 0)

        p.session_status = "done"
        p.save()

        return redirect('/#p' + str(patient_id))

    # ✏️ تعديل
    if "edit" in request.GET:
        p = Patient.objects.get(id=request.GET.get("edit"))
        p.session_status = "pending"
        p.save()
        return redirect('/#p' + request.GET.get("edit"))

    # ❌ لم تتم
    if "not_done" in request.GET:
        p = Patient.objects.get(id=request.GET.get("not_done"))
        p.session_status = "not_done"
        p.save()
        return redirect('/#p' + request.GET.get("not_done"))

    return render(request, 'home.html', {
        'today_patients': today_patients,
        'today_total':today_total,
        't':t
    })
# ================== ➕ ADD PATIENT ==================
@login_required
def add_patient(request):
    if request.method == 'POST':
        Patient.objects.create(
            first_name=request.POST.get('first_name'),
            last_name=request.POST.get('last_name'),
            treatment=request.POST.get('treatment'),
            next_appointment=request.POST.get('next_appointment') or date.today(),
            is_appointment=False   # 🔥 هذا مريض يومي
        )
        return redirect('/')

    return render(request, 'add_patient.html', {
        'today': date.today().isoformat()
    })
# ================== ⚡ QUICK APPOINTMENT ==================
@login_required
def quick_appointment(request):
    if request.method == 'POST':
        Patient.objects.create(
            first_name=request.POST.get('first_name'),
            last_name=request.POST.get('last_name'),
            treatment=request.POST.get('treatment'),
            total_amount=0,
            paid_amount=0,
            next_appointment=request.POST.get('appointment_date'),
            is_appointment=True   # 🔥 مهم جدا
        )
        return redirect('/appointments/')

    return render(request, 'quick_appointment.html')
# ================== 📆 UPCOMING ==================
@login_required
def upcoming_appointments(request):
    today = date.today()

    if request.method == 'POST':
        p = Patient.objects.get(id=request.POST.get('patient_id'))
        action = request.POST.get('action')
        new_date = request.POST.get('new_date')

        # 🔥 إضافة لليوم (تحويله لمريض يومي)
        if action == "to_today" and not p.added_to_today:
            Patient.objects.create(
            first_name=p.first_name,
            last_name=p.last_name,
            treatment=p.treatment,
            total_amount=0,
            paid_amount=0,
            next_appointment=today,
            is_appointment=False ,  # 👈 مريض اليوم
            has_appointment=True)
            p.added_to_today = True
            p.save()
        elif action == "reschedule" and new_date:
            p.next_appointment = new_date
            p.session_status = "pending"

        elif action in ["done", "not_done"]:
            p.session_status = action

        p.save()
        return redirect('/appointments/')

    patients = Patient.objects.filter(
        is_appointment=True
    ).order_by('-next_appointment')

    grouped = defaultdict(list)
    for p in patients:
        grouped[p.next_appointment].append(p)

    return render(request, 'appointments.html', {
        'grouped': dict(grouped),
        'today': today   # 🔥 مهم
    })
# ================== 💰 DEBTS ==================
@login_required
def debt_list(request):
    patients = Patient.objects.filter(
        Q(total_amount__gt=F('paid_amount')) |
        Q(is_manual_debt=True)
    ).distinct()

    return render(request, 'debt.html', {
        'patients': patients
    })
@login_required
def add_debt(request):
    if request.method == "POST":
        Patient.objects.create(
            first_name=request.POST.get("first_name"),
            last_name=request.POST.get("last_name"),
            treatment=request.POST.get("treatment"),
            total_amount=float(request.POST.get("total_amount") or 0),
            paid_amount=float(request.POST.get("paid_amount") or 0),
            is_manual_debt=True
        )
        return redirect('/debts/')

    return render(request, 'add_debt.html')

# ================== 🗑️ DELETE ==================
@login_required
def delete_patient(request):
    if request.method == "POST":
        patient = get_object_or_404(Patient, id=request.POST.get("id"))

       
        if patient.is_manual_debt:
            patient.paid_amount = patient.total_amount
            patient.is_manual_debt = False
            patient.save()

        else:
            patient.paid_amount = patient.total_amount
            patient.is_manual_debt = False
            patient.save()

    return redirect('/debts/')# ================== 👥 ALL PATIENTS ==================
@login_required
def all_patients(request):
    query = request.GET.get('q')
    selected_date = request.GET.get('date')

    # 👇 البداية دائماً من الصفر
    patients = Patient.objects.none()

    # 🔍 إذا بحث بالاسم فقط
    if query:
        patients = Patient.objects.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        )

    # 📅 إذا اختار تاريخ فقط
    elif selected_date:
        patients = Patient.objects.filter(
            next_appointment=selected_date
        )

    # 🚫 إذا لا يوجد أي بحث → لا شيء يظهر
    else:
        patients = Patient.objects.none()

    return render(request, 'all_patients.html', {
        'patients': patients,
        'query': query,
        'selected_date': selected_date,
        'today': date.today().isoformat()
    })
# ================== 📜 HISTORY ==================
@login_required
def patient_history(request):
    first = request.GET.get('first')
    last = request.GET.get('last')

    visits = Patient.objects.filter(
        first_name=first,
        last_name=last
    ).order_by('-next_appointment')

    return render(request, 'patient_history.html', {
        'visits': visits,
        'name': f"{first} {last}"
    })
# ================== 🔍 API ==================
@login_required
def search_patients_api(request):
    query = request.GET.get('q', '').strip()
    selected_date = request.GET.get('date', '').strip()

    # 🛑 إذا اختار تاريخ → نشتغل بالتاريخ فقط (نتجاهل الاسم)
    if selected_date:

        try:
            selected_date_obj = datetime.strptime(selected_date, "%Y-%m-%d").date()
        except:
            return JsonResponse({'patients': []})

        # 🚫 منع المستقبل
        if selected_date_obj > date.today():
            return JsonResponse({'patients': []})

        # ✅ فلترة صحيحة 100%
        patients = Patient.objects.filter(
            next_appointment=selected_date_obj
        )

        data = list(patients.values(
            'first_name',
            'last_name',
            'treatment',
            'total_amount',
            'paid_amount'
        ))

        return JsonResponse({
            'mode': 'date',
            'patients': data
        })

    # 🔍 البحث بالاسم (فقط إذا ما كاش تاريخ)
# 🔍 البحث بالاسم
    if query:
        parts = query.split()

        if len(parts) == 1:
            patients = Patient.objects.filter(
                Q(first_name__icontains=parts[0]) |
                Q(last_name__icontains=parts[0])
            )

        else:
            patients = Patient.objects.filter(
                (
                    Q(first_name__icontains=parts[0]) &
                    Q(last_name__icontains=parts[1])
                ) |
                (
                    Q(first_name__icontains=parts[1]) &
                    Q(last_name__icontains=parts[0])
                )
            )

        data = list(
            patients.values(
                'first_name',
                'last_name'
            ).distinct()
        )

        return JsonResponse({
            'mode': 'search',
            'patients': data
        })
    return JsonResponse({'patients': []}) 