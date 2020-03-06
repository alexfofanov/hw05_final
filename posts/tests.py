from django.test import TestCase, Client
from django.core import mail
from django.contrib.auth import get_user_model
from .models import Post, Group, User
from django.core.cache import cache


class TestAddImageToPost(TestCase):
    # тестирование загрузки и отображения картинок    
    def setUp(self):
        self.username = 'test_user'
        self.password = '12345#$XccMz'
        self.email = 'test_user@domain.com'
        self.text = 'Test post text.'
        self.group_name = 'test_group'
        self.client = Client()
        self.user = User.objects.create_user(username=self.username, email=self.email, password=self.password)
        self.group = Group.objects.create(title=self.group_name, slug=self.group_name)
        self.client.login(username=self.username, password=self.password)
        
        response = self.client.get('/')   
        with open('media/test_img.jpg', 'rb') as fp:
            response = self.client.post('/new/', {'group': self.group.id, 'text': self.text, 'image': fp})
            self.assertRedirects(response, '/')
        self.post = Post.objects.get(text=self.text)    

    def test_post_with_img(self):
        # проверяют страницу конкретной записи с картинкой: на странице есть тег <img>
        response = self.client.get(f'/{self.username}/{self.post.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<img ')   
        
    def test_index_img(self):
        # проверяют, что на главной странице пост с картинкой отображается корректно, с тегом <img>
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<img ', status_code=200)

    def test_profile_img(self):   
        # проверяют, что на странице профайла пост с картинкой отображается корректно, с тегом <img> 
        response = self.client.get(f'/{self.username}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<img ')

    def test_group_img(self):
        # проверяют, что на странице группы пост с картинкой отображается корректно, с тегом <img>
        response = self.client.get(f'/group/{self.group_name}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<img ')

    def test_format_non_img_defence(self):
        # проверяют, что срабатывает защита от загрузки файлов не-графических форматов
        with open('media/test_non_img.jpg', 'rb') as fp:
            response = self.client.post('/new/', {'group': self.group.id, 'text': self.text, 'image': fp})
        self.assertEqual(response.status_code, 200)

    def test_caching_posts_on_index_page(self):
        # проверка работы кэша         
        response = self.client.get('/')  
        self.assertNotContains(response, self.text) 
        cache.clear()
        response = self.client.get('/')
        self.assertContains(response, self.text)


class TestUserScripts(TestCase):
    def setUp(self):
        self.client = Client()
        self.username = 'test_user'
        self.password = '12345'
        self.email = 'test_user@domain.com'
        self.text = 'Test post text.'
        
        self.user = User.objects.create_user(username=self.username, email=self.email, password=self.password)
        self.post = Post.objects.create(author=self.user, text=self.text)
        self.client.login(username=self.username, password=self.password)
       

    def test_send_email(self):
        # Пользователь регистрируется и ему отправляется письмо с подтверждением регистрации
        mail.send_mail(
            'Тема письма', 'Текст письма.',
            'from@rocknrolla.net', ['to@mailservice.com'],
            fail_silently=False, # выводить описание ошибок
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Тема письма')

    def test_create_proile(self):
        # После регистрации пользователя создается его персональная страница (profile)
        response = self.client.get('/test_user/')
        self.assertEqual(response.status_code, 200)
    
    def test_public_new_post(self):
        # Авторизованный пользователь может опубликовать пост (new)
        response = self.client.get('/new/')
        self.assertEqual(response.status_code, 200)

    def test_unauthorized_user_new_post(self):
        # Неавторизованный посетитель не может опубликовать пост (его редиректит на страницу входа)    
        self.client.logout()
        response = self.client.get('/new/')
        self.assertRedirects(response, '/auth/login/?next=/new/')

    def test_new_post_publication_index(self):
        # После публикации поста новая запись появляется на главной странице сайта (index),
        response = self.client.get('/')
        self.assertContains(response, self.text)

    def test_new_post_publication_profile(self):
        # После публикации поста новая запись появляется на персональной странице пользователя (profile)
        response = self.client.get(f'/{self.username}/')
        self.assertContains(response, self.text)

    def test_new_post_publication_post_page(self):
        # После публикации поста новая запись появляется на отдельной странице поста (post)        
        response = self.client.get(f'/{self.username}/{self.post.id}/')
        self.assertContains(response, self.text)    
    
    def test_edit_post(self):
        # Авторизованный пользователь может отредактировать свой пост и его содержимое изменится
        edited_text = 'Test post text (edited).'
        with open('media/test_img.jpg', 'rb') as fp:
            response = self.client.post(f'/{self.username}/{self.post.id}/edit/', {'text': edited_text, 'image': fp})

        response = self.client.get(f'/{self.username}/{self.post.id}/')
        self.assertContains(response, edited_text)
        