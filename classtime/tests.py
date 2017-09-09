import datetime
import json

from django.contrib.auth.models import AnonymousUser
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIRequestFactory, force_authenticate

from DjangoReact import settings
from classtime.models import ClassTime
from classtime.views import ClassTimeViewSet
from core.models import User


class ClassTimeTest(TestCase):
    fixtures = ['classtime.json']

    def test_creating(self):
        classes_begin = ClassTime.objects.all().first()
        classes_end = ClassTime.objects.all().last()
        self.assertEqual(classes_begin.lesson_start, datetime.time(8, 30))
        self.assertEqual(classes_end.lesson_end, datetime.time(15, 50))

    def test_student_API(self):
        factory = APIRequestFactory()
        User(username='student1', password='qwert1234', staff="S").save()
        student = User.objects.get(username='student1')

        Token.objects.create(user=student)

        self.student_list_api(factory, student)
        self.student_detail_api(factory, student)

    def student_list_api(self, factory, student):
        class_time_list = ClassTimeViewSet.as_view({'get': 'list'})
        self._student_list_api_request(factory, student, class_time_list, '/classtimes', 8)
        self._student_list_api_request(factory, student, class_time_list,
                                       '/classtimes/?lesson_start__qte=8:30:00&'
                                       'lesson_end__lte=15:50:00', 8)
        self._student_list_api_request(factory, student, class_time_list,
                                       '/classtimes/?lesson_start__qte=10:15:00&'
                                       'lesson_end__lte=15:00:00', 5)
        self._student_list_api_request(factory, student, class_time_list,
                                       '/classtimes/?lesson_start__qte=9:16:00&'
                                       'lesson_end__lte=10:00:00', 0)

    def _student_list_api_request(self, factory, student, class_time_list,
                                  url, resp_len):
        student_request = factory.get(url)
        response_unauthenticated = class_time_list(student_request)
        self.assertEqual(response_unauthenticated.status_code,
                         status.HTTP_401_UNAUTHORIZED)
        force_authenticate(student_request, student, token=student.auth_token)
        response = class_time_list(student_request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), resp_len)

    def student_detail_api(self, factory, student):
        class_time_detail = ClassTimeViewSet.as_view({'get': 'retrieve'})
        student_request = factory.get('api/v0/classtimes')
        response_unauthenticated = class_time_detail(student_request, pk=1)
        self.assertEqual(response_unauthenticated.status_code, status.HTTP_401_UNAUTHORIZED)
        force_authenticate(student_request, student, student.auth_token)
        print('----')
        print('Only in this case permissions is reached')
        response = class_time_detail(student_request, pk=1)
        print('---')
        response.render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(json.loads(response.content), {
            "id": 1,
            "lesson_start": "08:30:00",
            "lesson_end": "09:15:00"
        })
        class_time_detail = ClassTimeViewSet.as_view({'post':'create'})

        student_request = factory.post('api/v0/classtimes',{'lesson_start':'20:00:00','lesson_end':'20:45:00'},format='json')
        force_authenticate(student_request,student,student.auth_token)
        response = class_time_detail(student_request)
        response.render()
        print(ClassTime.objects.all().last())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    def test_teacher_API(self):
        factory = APIRequestFactory()

        User(username='teacher1', password='qwert1234', staff="T").save()
        teacher = User.objects.get(username='teacher1')
        Token.objects.create(user=teacher)

        class_time_list = ClassTimeViewSet.as_view({'get': 'list'})
        class_time_detail = ClassTimeViewSet.as_view({'get': 'list'})

        teacher_request = factory.get('/classtimes')
        response_unauthenticated = class_time_list(teacher_request)
        self.assertEqual(response_unauthenticated.status_code, status.HTTP_401_UNAUTHORIZED)

        force_authenticate(teacher_request, teacher, token=teacher.auth_token)
        response = class_time_list(teacher_request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 8)
