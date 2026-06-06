from datetime import date
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.db.models import Q, Avg, Count
from django.contrib import messages
from django.core.exceptions import ValidationError

from .models import Atleta, Lesio, SessioEntrenament, Valoracio, Ubicacio, EstatActual, EstatAtleta, Exercici
from .forms import AtletaForm, LesioForm, SessioForm, ValoracioForm

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


class AtletaDeleteView(DeleteView):
    model = Atleta
    pk_url_kwarg = 'dni'
    success_url = reverse_lazy('atleta_list')

    def post(self, request, *args, **kwargs):
        atleta = self.get_object()
        messages.success(request, f"L'atleta {atleta.nom} ha estat eliminat.")
        return super().post(request, *args, **kwargs)


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
# 4. SESSIOENTRENAMENT CRUD VIEWS
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
            initial['atleta'] = get_object_or_4000(Atleta, dni_atleta=dni)
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
            context['fixed_atleta'] = get_object_or_4000(Atleta, dni_atleta=dni)
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
            initial['ubicacio'] = get_object_or_4000(Ubicacio, id=ub_id)
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_tab'] = 'ubicacions'
        
        ub_id = self.request.GET.get('ubicacio')
        if ub_id:
            context['fixed_ubicacio'] = get_object_or_4000(Ubicacio, id=ub_id)
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
