from django.contrib.admin.views.main import IS_POPUP_VAR, TO_FIELD_VAR
from django.contrib.admin.widgets import ForeignKeyRawIdWidget, ManyToManyRawIdWidget, RelatedFieldWidgetWrapper
from django.utils.html import escape
from django.utils.text import Truncator

from bson.dbref import DBRef


class ReferenceRawIdWidget(ForeignKeyRawIdWidget):
    """
    A Widget for displaying ReferenceFields in the "raw_id" interface rather than
    in a <select> box.
    """
    def render(self, name, value, attrs=None):
        if attrs is None:
            attrs = {}
        if 'style' not in attrs:
            attrs['style'] = 'width:30em;'
        if isinstance(value, DBRef):
            value = value.id
        return super(ReferenceRawIdWidget, self).render(name=name, value=value, attrs=attrs)

    def url_parameters(self):
        #from django.contrib.admin.views.main import TO_FIELD_VAR
        params = self.base_url_parameters()
        # There are no reverse relations in mongo. Still need to figure out what
        # the url param does though.
        #params.update({TO_FIELD_VAR: self.rel.get_related_field().name})
        return params

    def label_for_value(self, value):
        #key = self.rel.get_related_field().name
        if isinstance(value, DBRef):
            value = value.id
        try:
            obj = self.rel.to.objects().get(**{'pk': value})
            return '&nbsp;<strong>%s</strong>' % escape(Truncator(obj).words(14, truncate='...'))
        except (ValueError, self.rel.to.DoesNotExist):
            return ''


class MultiReferenceRawIdWidget(ManyToManyRawIdWidget):
    def render(self, name, value, attrs=None):
        if attrs is None:
            attrs = {}
        if 'style' not in attrs:
            attrs['style'] = 'width:40em;'
        return super(MultiReferenceRawIdWidget, self).render(name=name, value=value, attrs=attrs)


class MongoRelatedFieldWidgetWrapper(RelatedFieldWidgetWrapper):
    """
    This is a small hack to make it possible to add/change/delete a related field.

    NB: only add is supported for now.
    """
    def render(self, name, value, *args, **kwargs):
        rel_opts = self.rel.model._meta
        info = (rel_opts.app_label, rel_opts.model_name)
        self.widget.choices = self.choices
        url_params = '&'.join("%s=%s" % param for param in [
            (TO_FIELD_VAR, "%s__%s" % (self.rel.parent_document.__name__, self.rel.model.__name__)),
            (IS_POPUP_VAR, 1),
        ])
        context = {
            'widget': self.widget.render(name, value, *args, **kwargs),
            'name': name,
            'url_params': url_params,
            'model': rel_opts.verbose_name,
        }
        if self.can_change_related:
            change_related_template_url = self.get_related_url(info, 'change', '__fk__')
            context.update(
                can_change_related=True,
                change_related_template_url=change_related_template_url,
            )
        if self.can_add_related:
            add_related_url = self.get_related_url(info, 'add')
            context.update(
                can_add_related=True,
                add_related_url=add_related_url,
            )
        if self.can_delete_related:
            delete_related_template_url = self.get_related_url(info, 'delete', '__fk__')
            context.update(
                can_delete_related=True,
                delete_related_template_url=delete_related_template_url,
            )
        return mark_safe(render_to_string(self.template, context))
