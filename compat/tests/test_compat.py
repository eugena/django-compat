from django.test import TestCase
import django
from django.contrib.auth.views import logout
from django.core.urlresolvers import NoReverseMatch

from compat import resolve_url

import compat

from .models import UnimportantThing

class CompatTests(TestCase):

    def test_compat(self):
        from compat import import_module
        from compat import __all__

        compat = import_module('compat')

        for n in __all__:
            getattr(compat, n)

        self.assertTrue(True)

    def test_format_html(self):
        """
        Test: format_html
        url: https://github.com/django/django/blob/stable/1.8.x/tests/utils_tests/test_html.py#L44-L53

        """

        from django.utils import html

        from compat import format_html

        self.assertEqual(
            format_html("{0} {1} {third} {fourth}",
                             "< Dangerous >",
                             html.mark_safe("<b>safe</b>"),
                             third="< dangerous again",
                             fourth=html.mark_safe("<i>safe again</i>")
                             ),
            "&lt; Dangerous &gt; <b>safe</b> &lt; dangerous again <i>safe again</i>"
        )

    def test_url_path(self):
        """
        Tests that passing a URL path to ``resolve_url`` will result in the
        same url.
        """
        self.assertEqual('/something/', resolve_url('/something/'))

    def test_relative_path(self):
        """
        Tests that passing a relative URL path to ``resolve_url`` will result
        in the same url.
        """
        self.assertEqual('../', resolve_url('../'))
        self.assertEqual('../relative/', resolve_url('../relative/'))
        self.assertEqual('./', resolve_url('./'))
        self.assertEqual('./relative/', resolve_url('./relative/'))

    def test_full_url(self):
        """
        Tests that passing a full URL to ``resolve_url`` will result in the
        same url.
        """
        url = 'http://example.com/'
        self.assertEqual(url, resolve_url(url))

    def test_model(self):
        """
        Tests that passing a model to ``resolve_url`` will result in
        ``get_absolute_url`` being called on that model instance.
        """
        m = UnimportantThing(importance=1)
        self.assertEqual(m.get_absolute_url(), resolve_url(m))

    def test_view_function(self):
        """
        Tests that passing a view name to ``resolve_url`` will result in the
        URL path mapping to that view name.
        """
        resolved_url = resolve_url(logout)
        self.assertEqual('/accounts/logout/', resolved_url)

    '''
    incompatible with lower django versions
    def test_lazy_reverse(self):
        """
        Tests that passing the result of reverse_lazy is resolved to a real URL
        string.
        """
        from django.utils import six
        resolved_url = resolve_url(reverse_lazy('logout'))
        self.assertIsInstance(resolved_url, six.text_type)
        self.assertEqual('/accounts/logout/', resolved_url)
    '''

    def test_valid_view_name(self):
        """
        Tests that passing a view function to ``resolve_url`` will result in
        the URL path mapping to that view.
        """
        resolved_url = resolve_url('django.contrib.auth.views.logout')
        self.assertEqual('/accounts/logout/', resolved_url)

    def test_domain(self):
        """
        Tests that passing a domain to ``resolve_url`` returns the same domain.
        """
        self.assertEqual(resolve_url('example.com'), 'example.com')

    def test_non_view_callable_raises_no_reverse_match(self):
        """
        Tests that passing a non-view callable into ``resolve_url`` raises a
        ``NoReverseMatch`` exception.
        """
        with self.assertRaises(NoReverseMatch):
            resolve_url(lambda: 'asdf')

    def test_commit_on_success(self):
        """
        Test of commit_on_success
        """
        @compat.commit_on_success
        def db_action():
            m = UnimportantThing(pk=1, importance=1)
            m.save()

        db_action()
        self.assertEqual(UnimportantThing.objects.get(pk=1).importance, 1)

    def test_commit(self):
        """
        Test of commit
        """
        m = UnimportantThing(pk=2, importance=2)
        m.save()
        compat.commit()
        self.assertEqual(UnimportantThing.objects.get(pk=2).importance, 2)

    def test_rollback_with_sid(self):
        """
        Test of rollback with transaction savepoint
        """
        @compat.commit_on_success
        def db_action():
            m = UnimportantThing(pk=3, importance=3)
            m.save()
            return m

        @compat.commit_on_success
        def db_action_with_rollback(m):
            m.importance = 5
            sid = django.db.transaction.savepoint()
            m.save()
            compat.rollback(None, sid)

        if django.VERSION < (1, 5):  # Rollback doesn't work with SQLite
            return

        m = db_action()
        db_action_with_rollback(m)
        self.assertEqual(UnimportantThing.objects.get(pk=3).importance, 3)

    def test_rollback_without_sid(self):
        """
        Test of rollback without transaction savepoint
        """
        @compat.commit_on_success
        def db_action():
            m = UnimportantThing(pk=4, importance=4)
            m.save()
            return m

        @compat.commit_on_success
        def db_action_with_rollback(m):
            m.importance = 5
            m.save()
            compat.rollback()

        if django.VERSION < (1, 8):  # Rollback doesn't work after .save() if an exception isn't thrown
            return

        m = db_action()
        db_action_with_rollback(m)
        self.assertEqual(UnimportantThing.objects.get(pk=4).importance, 4)



