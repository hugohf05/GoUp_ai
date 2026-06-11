import json
from datetime import date
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.db.models import Q, Avg, Count
from django.contrib import messages
from django.core.exceptions import ValidationError

from .models import Atleta, Lesio, SessioEntrenament, Valoracio, Ubicacio, EstatActual, EstatAtleta, Exercici, RegistreDiari, InformeIA, Forca, Resistencia, Alimentacio
from .forms import AtletaForm, LesioForm, SessioForm, ValoracioForm, RegistreDiariForm, ExerciciForm, AlimentacioForm

# --------------------------------------------------------------------------
# 1. DASHBOARD VIEW
# --------------------------------------------------------------------------
class DashboardView(TemplateView):
    template_name = 'core/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_tab'] = 'dashboard'
        context['total_atletes'] = Atleta.objects.count()
        context['total_lesionats'] = Atleta.objects.filter(estat=EstatAtleta.LESIONAT).count()
        context['total_sessions'] = SessioEntrenament.objects.count()
        context['total_valoracions'] = Valoracio.objects.count()
        
        # Recent activity feeds (optimized queries)
        context['recent_sessions'] = SessioEntrenament.objects.select_related('atleta', 'ubicacio').order_by('-data', '-id')[:5]
        context['active_lesions'] = Lesio.objects.select_related('atleta').filter(estat_actual=EstatActual.ACTIVA).order_by('-data_inici')[:5]
        return context

from django.http import JsonResponse
from django.views import View

class DashboardDataView(View):
    def get(self, request, *args, **kwargs):
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models import Count

        # Gràfic 1: Activitat d'Entrenaments (Últims 7 dies)
        today = timezone.now().date()
        days = [today - timedelta(days=i) for i in range(6, -1, -1)]
        
        sessions_data = []
        labels_days = []
        for day in days:
            count = SessioEntrenament.objects.filter(data=day).count()
            sessions_data.append(count)
            labels_days.append(day.strftime("%d/%m"))
            
        # Gràfic 2: Distribució d'Objectius d'Atletes
        objectius_data = Atleta.objects.values('objectiu').annotate(count=Count('dni_atleta')).order_by('-count')[:5]
        labels_obj = [o['objectiu'] if o['objectiu'] else 'Sense objectiu' for o in objectius_data]
        data_obj = [o['count'] for o in objectius_data]

        data = {
            'total_atletes': Atleta.objects.count(),
            'total_lesionats': Atleta.objects.filter(estat=EstatAtleta.LESIONAT).count(),
            'total_sessions': SessioEntrenament.objects.count(),
            'total_valoracions': Valoracio.objects.count(),
            'chart_sessions': {
                'labels': labels_days,
                'data': sessions_data
            },
            'chart_objectius': {
                'labels': labels_obj,
                'data': data_obj
            }
        }
        return JsonResponse(data)


# --------------------------------------------------------------------------
# 2. ATLETA CRUD VIEWS
# --------------------------------------------------------------------------
class AtletaListView(ListView):
    model = Atleta
    template_name = 'core/atleta_list.html'
    context_object_name = 'athletes'
    paginate_by = 15

    def get_queryset(self):
        queryset = super().get_queryset().order_by('nom')
        self.query_search = self.request.GET.get('q', '').strip()
        
        if self.query_search:
            queryset = queryset.filter(
                Q(dni_atleta__icontains=self.query_search) |
                Q(nom__icontains=self.query_search) |
                Q(correu__icontains=self.query_search)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_tab'] = 'atletes'
        context['query_search'] = self.query_search
        
        # Calcular edat dinàmicament per a cada atleta en el queryset
        today = date.today()
        for atleta in context['athletes']:
            dob = atleta.data_naixement
            atleta.edat = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return context


class AtletaDetailView(DetailView):
    model = Atleta
    template_name = 'core/atleta_detail.html'
    context_object_name = 'athlete'
    pk_url_kwarg = 'dni'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_tab'] = 'atletes'
        
        # Calcular edat
        dob = self.object.data_naixement
        today = date.today()
        context['athlete'].edat = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return context


class AtletaCreateView(CreateView):
    model = Atleta
    form_class = AtletaForm
    template_name = 'core/atleta_form.html'
    success_url = reverse_lazy('atleta_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_tab'] = 'atletes'
        context['is_edit'] = False
        return context

    def form_valid(self, form):
        messages.success(self.request, f"L'atleta {form.cleaned_data['nom']} s'ha registrat correctament.")
        return super().form_valid(form)


class AtletaUpdateView(UpdateView):
    model = Atleta
    form_class = AtletaForm
    template_name = 'core/atleta_form.html'
    pk_url_kwarg = 'dni'
    success_url = reverse_lazy('atleta_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_tab'] = 'atletes'
        context['is_edit'] = True
        return context

    def form_valid(self, form):
        messages.success(self.request, f"El perfil de {form.cleaned_data['nom']} s'ha actualitzat correctament.")
        return super().form_valid(form)


from django.views import View

class AtletaDeleteView(View):
    def get(self, request, dni, *args, **kwargs):
        from django.db.models import RestrictedError, ProtectedError
        atleta = get_object_or_404(Atleta, dni_atleta=dni)
        nom_atleta = atleta.nom
        try:
            atleta.delete()
            messages.success(request, f"L'atleta {nom_atleta} ha estat eliminat.")
        except (RestrictedError, ProtectedError):
            messages.error(request, f"No es pot eliminar l'atleta perquè té registres vinculats que ho impedeixen.")
        return redirect('atleta_list')


# --------------------------------------------------------------------------
# 3. LESIO CRUD VIEWS
# --------------------------------------------------------------------------
class LesioListView(ListView):
    model = Lesio
    template_name = 'core/lesio_list.html'
    context_object_name = 'lesions'
    paginate_by = 15

    def get_queryset(self):
        queryset = super().get_queryset().select_related('atleta').order_by('-data_inici', '-id_lesio')
        self.query_search = self.request.GET.get('q', '').strip()
        self.status_filter = self.request.GET.get('status', '').strip()

        if self.query_search:
            queryset = queryset.filter(
                Q(zona_afectada__icontains=self.query_search) |
                Q(atleta__nom__icontains=self.query_search) |
                Q(atleta__dni_atleta__icontains=self.query_search)
            )
        
        if self.status_filter:
            queryset = queryset.filter(estat_actual=self.status_filter)
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_tab'] = 'lesions'
        context['query_search'] = self.query_search
        context['status_filter'] = self.status_filter
        return context


class LesioCreateView(CreateView):
    model = Lesio
    form_class = LesioForm
    template_name = 'core/lesio_form.html'

    def get_success_url(self):
        # Redirigir al perfil de l'atleta afectat
        return reverse('atleta_detail', kwargs={'dni': self.object.atleta.dni_atleta})

    def get_initial(self):
        initial = super().get_initial()
        dni = self.request.GET.get('atleta')
        if dni:
            atleta = get_object_or_404(Atleta, dni_atleta=dni)
            initial['atleta'] = atleta
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_tab'] = 'lesions'
        context['is_edit'] = False
        
        dni = self.request.GET.get('atleta')
        if dni:
            context['fixed_atleta'] = get_object_or_404(Atleta, dni_atleta=dni)
        return context

    def form_valid(self, form):
        lesio = form.save(commit=False)
        # Calcular el següent id_lesio automàticament per a aquest atleta
        from django.db.models import Max
        max_id = Lesio.objects.filter(atleta=lesio.atleta).aggregate(Max('id_lesio'))['id_lesio__max']
        lesio.id_lesio = (max_id or 0) + 1
            
        lesio.save()
        messages.success(self.request, f"S'ha registrat la lesió a la zona '{lesio.zona_afectada}' per a {lesio.atleta.nom}.")
        return redirect(self.get_success_url())


class LesioUpdateView(UpdateView):
    model = Lesio
    form_class = LesioForm
    template_name = 'core/lesio_form.html'

    def get_object(self, queryset=None):
        # La PK a PostgreSQL és compound (atleta_id, id_lesio).
        # En Django utilitzem els paràmetres de la URL.
        dni = self.kwargs.get('dni')
        id_les = self.kwargs.get('id_lesio')
        return get_object_or_404(Lesio, atleta_id=dni, id_lesio=id_les)

    def get_success_url(self):
        return reverse('atleta_detail', kwargs={'dni': self.object.atleta.dni_atleta})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_tab'] = 'lesions'
        context['is_edit'] = True
        return context

    def form_valid(self, form):
        les = form.save()
        messages.success(self.request, f"S'ha modificat el registre de lesió per a {les.atleta.nom}.")
        return redirect(self.get_success_url())


# --------------------------------------------------------------------------
# 4. ALIMENTACIO CRUD VIEWS
# --------------------------------------------------------------------------
class AlimentacioCreateView(CreateView):
    model = Alimentacio
    form_class = AlimentacioForm
    template_name = 'core/alimentacio_form.html'

    def get_success_url(self):
        return reverse('atleta_detail', kwargs={'dni': self.kwargs['dni']})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_tab'] = 'alimentacio'
        context['is_edit'] = False
        context['fixed_atleta'] = get_object_or_404(Atleta, dni_atleta=self.kwargs['dni'])
        return context

    def form_valid(self, form):
        alimentacio = form.save(commit=False)
        atleta = get_object_or_404(Atleta, dni_atleta=self.kwargs['dni'])
        alimentacio.atleta = atleta
        alimentacio.save()
        messages.success(self.request, f"S'ha creat la pauta d'alimentació per a {atleta.nom}.")
        return redirect(self.get_success_url())

class AlimentacioUpdateView(UpdateView):
    model = Alimentacio
    form_class = AlimentacioForm
    template_name = 'core/alimentacio_form.html'

    def get_object(self, queryset=None):
        return get_object_or_404(Alimentacio, atleta__dni_atleta=self.kwargs['dni'])

    def get_success_url(self):
        return reverse('atleta_detail', kwargs={'dni': self.kwargs['dni']})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_tab'] = 'alimentacio'
        context['is_edit'] = True
        context['fixed_atleta'] = get_object_or_404(Atleta, dni_atleta=self.kwargs['dni'])
        return context

    def form_valid(self, form):
        alimentacio = form.save()
        messages.success(self.request, f"S'ha actualitzat la pauta d'alimentació de {alimentacio.atleta.nom}.")
        return redirect(self.get_success_url())


# --------------------------------------------------------------------------
# 5. SESSIOENTRENAMENT CRUD VIEWS
# --------------------------------------------------------------------------
class SessioListView(ListView):
    model = SessioEntrenament
    template_name = 'core/sessio_list.html'
    context_object_name = 'sessions'
    paginate_by = 15

    def get_queryset(self):
        queryset = super().get_queryset().select_related('atleta', 'ubicacio').prefetch_related('exercicis').order_by('-data', '-id')
        self.query_search = self.request.GET.get('q', '').strip()
        if self.query_search:
            queryset = queryset.filter(
                Q(atleta__nom__icontains=self.query_search) |
                Q(atleta__dni_atleta__icontains=self.query_search)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_tab'] = 'sessions'
        context['query_search'] = self.query_search
        return context


class SessioCreateView(CreateView):
    model = SessioEntrenament
    form_class = SessioForm
    template_name = 'core/sessio_form.html'
    success_url = reverse_lazy('sessio_list')

    def get_initial(self):
        initial = super().get_initial()
        dni = self.request.GET.get('atleta')
        if dni:
            initial['atleta'] = get_object_or_404(Atleta, dni_atleta=dni)
        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Passar l'atleta al formulari per filtrar els exercicis per rendiment
        dni = self.request.GET.get('atleta') or (self.request.POST.get('atleta') if self.request.method == 'POST' else None)
        if dni:
            try:
                kwargs['athlete'] = Atleta.objects.get(dni_atleta=dni)
            except Atleta.DoesNotExist:
                pass
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_tab'] = 'sessions'
        
        dni = self.request.GET.get('atleta')
        if dni:
            context['fixed_atleta'] = get_object_or_404(Atleta, dni_atleta=dni)
        return context

    def form_valid(self, form):
        sessio = form.save()
        messages.success(self.request, f"S'ha registrat una sessió d'entrenament per a {sessio.atleta.nom}.")
        
        # Si s'ha especificat enllaçar des del perfil de l'atleta, hi tornem
        dni = self.request.GET.get('atleta')
        if dni:
            return redirect('atleta_detail', dni=dni)
        return super().form_valid(form)


# --------------------------------------------------------------------------
# 5. UBICACIONS & VALORACIONS
# --------------------------------------------------------------------------
class UbicacioListView(ListView):
    model = Ubicacio
    template_name = 'core/ubicacio_list.html'
    context_object_name = 'locations'
    paginate_by = 15

    def get_queryset(self):
        # Anotem cada ubicació amb la seva valoració mitjana i número de vots realitzats
        queryset = Ubicacio.objects.annotate(
            avg_rating=Avg('valoracio__valoracio'),
            num_ratings=Count('valoracio')
        ).order_by('-num_ratings', '-avg_rating')

        self.query_search = self.request.GET.get('q', '').strip()
        self.type_filter = self.request.GET.get('type', '').strip()

        if self.query_search:
            queryset = queryset.filter(adreca__icontains=self.query_search)
        
        if self.type_filter:
            queryset = queryset.filter(tipus_ubicacio=self.type_filter)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_tab'] = 'ubicacions'
        context['query_search'] = self.query_search
        context['type_filter'] = self.type_filter
        return context


class ValoracioCreateView(CreateView):
    model = Valoracio
    form_class = ValoracioForm
    template_name = 'core/valoracio_form.html'
    success_url = reverse_lazy('ubicacio_list')

    def get_initial(self):
        initial = super().get_initial()
        ub_id = self.request.GET.get('ubicacio')
        if ub_id:
            initial['ubicacio'] = get_object_or_404(Ubicacio, id=ub_id)
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_tab'] = 'ubicacions'
        
        ub_id = self.request.GET.get('ubicacio')
        if ub_id:
            context['fixed_ubicacio'] = get_object_or_404(Ubicacio, id=ub_id)
        return context

    def form_valid(self, form):
        try:
            # El clean() i save() del model faran saltar ValidationError (RI-1)
            # si l'atleta no s'ha entrenat mai a la ubicació.
            form.instance.full_clean()
            form.save()
            messages.success(self.request, f"Moltes gràcies per valorar l'instal·lació. S'ha registrat la teva opinió.")
            return redirect(self.success_url)
        except ValidationError as e:
            # Convertim els errors del model en errors del formulari per mostrar-los a l'usuari de forma neta
            for field, errors in e.message_dict.items():
                for error in errors:
                    form.add_error(field, error)
            return self.form_invalid(form)


# --------------------------------------------------------------------------
# 6. REGISTRES DIARIS & INFORME IA VIEWS
# --------------------------------------------------------------------------
class RegistreDiariCreateView(CreateView):
    model = RegistreDiari
    form_class = RegistreDiariForm
    template_name = 'core/registre_diari_form.html'

    def get_initial(self):
        initial = super().get_initial()
        dni = self.kwargs.get('dni')
        if dni:
            atleta = get_object_or_404(Atleta, dni_atleta=dni)
            initial['atleta'] = atleta
        initial['data'] = date.today()
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_tab'] = 'atletes'
        dni = self.kwargs.get('dni')
        if dni:
            context['athlete'] = get_object_or_404(Atleta, dni_atleta=dni)
        return context

    def form_valid(self, form):
        registre = form.save(commit=False)
        # Sincronització de l'atleta des de la URL per seguretat
        dni = self.kwargs.get('dni')
        if dni:
            registre.atleta = get_object_or_404(Atleta, dni_atleta=dni)
        
        try:
            registre.full_clean()
            registre.save()
        except ValidationError as e:
            for field, errors in e.message_dict.items():
                for error in errors:
                    form.add_error(field, error)
            return self.form_invalid(form)

        # Generar InformeIA de forma automatitzada
        energia = float(registre.nivell_energia)
        estres = float(registre.nivell_estres)
        recuperacio = float(registre.estat_recuperacio_descans)
        nutricio = float(registre.adaptabilitat_alimentacio)

        # 1. Recomanació d'entrenament
        if energia >= 4.0 and estres < 2.5:
            rec_entrenament = (
                "Nivell d'energia excel·lent i baix estrès. Avui és un dia ideal per a una sessió de "
                "potència, sèries d'alta intensitat o una tirada de gran volum. El teu cos està "
                "completament preparat per absorbir estímuls elevats d'entrenament."
            )
        elif energia <= 2.0 or estres >= 4.0:
            rec_entrenament = (
                "Energia significativament baixa o nivell d'estrès molt elevat. Es desaconsella "
                "qualsevol treball d'alta intensitat o força màxima per evitar el sobreentrenament o "
                "lesions. Opta per una sessió molt suau de recuperació activa (ioga, estiraments, "
                "mobilitat de baix impacte) o directament descans complet."
            )
        else:
            rec_entrenament = (
                "Estat de vitalitat moderat. Recomanem un entrenament de manteniment a intensitat controlada. "
                "Centra't en la tècnica dels exercicis i evita arribar a l'error muscular. Escolta el teu cos "
                "durant l'escalfament i modula les càrregues en conseqüència."
            )

        # 2. Recomanació d'alimentació
        if nutricio >= 85.0:
            rec_alimentacio = (
                f"Adherència excel·lent a la teva planificació nutricional ({nutricio}%). Mantingues "
                "aquest patró d'àpats. Assegura't de cobrir la ingesta de líquids necessària, afegint "
                "electròlits si realitzes entrenaments de més de 90 minuts."
            )
        elif nutricio < 70.0:
            rec_alimentacio = (
                f"L'adherència dietètica avui ha estat baixa ({nutricio}%). Per compensar i donar suport "
                "a la recuperació cel·lular, prioritza en els propers àpats fonts de proteïna magra "
                "(gall dindi, peix o tofu) i carbohidrats complexos de fàcil digestió. Redueix totalment "
                "els ultraprocessats i greixos saturats."
            )
        else:
            rec_alimentacio = (
                f"Bona adherència a la dieta ({nutricio}%). Intenta planificar millor el 'timing' dels "
                "nutrients abans i després de la sessió. Augmenta la ingesta de carbohidrats d'index "
                "glucèmic mitjà per reposar completament el glucogen muscular."
            )

        # 3. Recomanació de descans
        if recuperacio >= 4.0:
            rec_descans = (
                "Estat de recuperació nocturna excel·lent. El son ha estat profund i reparador. "
                "El teu sistema nerviós autònom es troba en un perfecte equilibri simpàtic-parasimpàtic. "
                "Continua mantenint la mateixa rutina d'higiene del son."
            )
        elif recuperacio <= 2.5:
            rec_descans = (
                "Valors de recuperació i descans per sota de la mitjana. S'observa una possible falta "
                "de son profund o acumulació de fatiga. Prioritza avui anar a dormir més d'hora del que "
                "és habitual, evita l'ús de pantalles o dispositius electrònics almenys 60 minuts abans d'adormir-te "
                "i considera fer una migdiada reparadora d'uns 20 minuts al migdia."
            )
        else:
            rec_descans = (
                "Nivell de recuperació mitjà. L'organisme està recuperant-se de forma progressiva. "
                "Evita sopars copiosos o molt tardans i mantingues la teva habitació a una temperatura fresca "
                "per afavorir una millor qualitat de descans durant la nit."
            )

        InformeIA.objects.create(
            registre_diari=registre,
            recomanacio_entrenament=rec_entrenament,
            recomanacio_alimentacio=rec_alimentacio,
            recomanacio_descans=rec_descans
        )

        messages.success(self.request, "S'ha registrat el teu estat diari i l'IA ha generat un nou informe de recomanacions.")
        return redirect('atleta_detail', dni=registre.atleta.dni_atleta)


class InformeIADetailView(DetailView):
    model = InformeIA
    template_name = 'core/informe_ia_detail.html'
    context_object_name = 'informe'

    def get_object(self, queryset=None):
        registre_id = self.kwargs.get('registre_id')
        return get_object_or_404(InformeIA, registre_diari_id=registre_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_tab'] = 'atletes'
        return context

# --------------------------------------------------------------------------
# Exercici Views
# --------------------------------------------------------------------------
from django.db import transaction
from django.http import HttpResponseBadRequest

class ExerciciCreateView(CreateView):
    model = Exercici
    form_class = ExerciciForm
    template_name = 'core/exercici_form.html'
    success_url = reverse_lazy('dashboard')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_tab'] = 'exercicis'
        return context

    @transaction.atomic
    def form_valid(self, form):
        self.object = form.save()
        
        series_data_str = self.request.POST.get('series_data', '[]')
        try:
            series_data = json.loads(series_data_str)
        except json.JSONDecodeError:
            return HttpResponseBadRequest("Invalid JSON data for series")
            
        num_serie = 1
        for s in series_data:
            tipus = s.get('tipus')
            if tipus == 'forca':
                Forca.objects.create(
                    exercici=self.object,
                    num_serie=num_serie,
                    grup_muscular=s.get('grup_muscular', ''),
                    pes=s.get('pes', 0) if s.get('pes') else 0,
                    rpe=s.get('rpe', 0) if s.get('rpe') else 0
                )
            elif tipus == 'resistencia':
                Resistencia.objects.create(
                    exercici=self.object,
                    num_serie=num_serie,
                    duracio=s.get('duracio', '00:00:00'),
                    tipus_superficie=s.get('tipus_superficie', ''),
                    distancia=s.get('distancia', 0) if s.get('distancia') else 0,
                    desnivell=s.get('desnivell') or None,
                    freq_cardiaca_mitjana=s.get('freq_cardiaca_mitjana', 0) if s.get('freq_cardiaca_mitjana') else 0
                )
            num_serie += 1
            
        messages.success(self.request, f"L'exercici '{self.object.nom}' i les seves {num_serie - 1} sèries s'han desat correctament.")
        return super().form_valid(form)
