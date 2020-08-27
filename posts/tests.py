from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from .models import Follow, Group, Post

User = get_user_model()


class UserTest(TestCase):
    def setUp(self):
        self.client_unauthorized = Client()
        self.client_authorized = Client()
        self.user = User.objects.create_user(
            username="test_user", email="connor.s@skynet.com", password="123"
        )
        self.client_authorized.force_login(self.user)
        self.group = Group.objects.create(
            title="test_title_group", slug="test_slug_group"
        )

    def check_post(self, url, text, user, group=None):
        resp = self.client_authorized.get(url)
        self.assertEqual(resp.status_code, 200)
        paginator = resp.context.get("paginator")
        if paginator is not None:
            self.assertEqual(paginator.count, 1)
            post = resp.context["page"][0]
        else:
            post = resp.context["post"]
        self.assertEqual(post.text, text)
        self.assertEqual(post.author, user)
        self.assertEqual(post.group, group)

    def test_profile(self):
        resp = self.client_authorized.get(
            reverse("profile", args=[self.user.username]))
        self.assertEqual(resp.status_code, 200)

    def test_create_post(self):
        TEST_TEXT = "создаем тестовый пост"
        resp = self.client_authorized.post(
            reverse("new_post"),
            {"text": TEST_TEXT, "group": self.group.pk},
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.check_post(reverse("index"), TEST_TEXT, self.user, self.group)

    def test_redirect(self):
        TEST_TEXT = "создаем тестовый пост"
        url_new_post = reverse("new_post")
        resp = self.client_unauthorized.post(
            url_new_post, {"text": TEST_TEXT, "group": self.group.pk}
        )
        self.assertRedirects(resp, f"/auth/login/?next={url_new_post}")
        resp_index = self.client_unauthorized.get(reverse("index"))
        posts = resp_index.context["paginator"]
        self.assertEqual(posts.count, 0)

    def test_accept_post(self):
        TEST_TEXT = "Какой-то текст"
        self.post = Post.objects.create(text=TEST_TEXT, author=self.user)
        self.check_post(reverse("index"), TEST_TEXT, self.user)
        self.check_post(
            reverse("profile", args=[self.user.username]), TEST_TEXT, self.user
        )
        self.check_post(
            reverse("post", args=[self.user.username, self.post.id]),
            TEST_TEXT,
            self.user,
        )

    def test_edit_post(self):
        TEST_TEXT = "Какой-то текст"
        NEW_TEST_TEXT = "Это новый текст!"
        self.group_new = Group.objects.create(
            title="new_test_group", slug="new_test_slug"
        )
        self.post = Post.objects.create(text=TEST_TEXT, author=self.user)
        response = self.client_authorized.post(
            reverse("post_edit", args=[self.user.username, self.post.id]),
            {"text": NEW_TEST_TEXT, "group": self.group_new.pk},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.check_post(reverse("index"), NEW_TEST_TEXT, self.user,
                        self.group_new)
        self.check_post(
            reverse("profile", args=[self.user.username]),
            NEW_TEST_TEXT,
            self.user,
            self.group_new,
        )
        self.check_post(
            reverse("post", args=[self.user.username, self.post.id]),
            NEW_TEST_TEXT,
            self.user,
            self.group_new,
        )


class TestErrors(TestCase):
    def setUp(self):
        self.client = Client()
        self.test_url = "invalid address"

    def test_404(self):
        resp = self.client.get(self.test_url)
        self.assertEqual(resp.status_code, 404)


class TestImage(TestCase):
    def setUp(self):
        self.client_authorized = Client()
        self.user = User.objects.create_user(
            username="test_user", email="connor.s@skynet.com", password="123"
        )
        self.post = Post.objects.create(text="test_text", author=self.user)
        self.client_authorized.force_login(self.user)

        self.group = Group.objects.create(
            title="test_title_group", slug="test_slug_group"
        )
        self.tag = "<img"

    def test_post_index_group_profile_has_an_img_tag(self):
        img = SimpleUploadedFile(
            "test.jpg",
            open("media/posts/test_img.jpg", "rb").read(),
            content_type="image/jpg",
        )
        post = Post.objects.create(
            text="test_text", author=self.user, image=img, group=self.group
        )

        urls = [
            reverse("index"),
            reverse("post", args=[self.user.username, post.id]),
            reverse("group", args=[self.group.slug]),
            reverse("profile", args=[self.user.username]),
        ]

        cache.clear()

        for url in urls:
            with self.subTest(url=url):
                resp = self.client_authorized.get(url)
                self.assertContains(resp, self.tag)

    def test_ungraphical_file_upload(self):
        not_img = SimpleUploadedFile("test_img.txt", content=b"abc")
        resp = self.client_authorized.post(
            reverse("new_post"), {'text': 'test_text', 'image': not_img})

        self.assertFormError(
            resp,
            "form",
            "image",
            (
                "Загрузите правильное изображение. "
                "Файл, который вы загрузили, поврежден или "
                "не является изображением."
            ),
        )


class TestCache(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="test_user")
        self.client = Client()
        self.client.force_login(self.user)

    def test_cache(self):
        self.client.post(reverse("new_post"), {"text": "тест_1"})
        resp_1 = self.client.get(reverse("index"))
        self.assertContains(resp_1, "тест_1")
        self.client.post(reverse("new_post"), {"text": "тест_2"})
        resp_2 = self.client.get(reverse("index"))
        self.assertNotContains(resp_2, "тест_2")
        cache.clear()
        resp_3 = self.client.get(reverse("index"))
        self.assertContains(resp_3, "тест_2")


class TestFollower(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="test_user_1")
        self.user_we_are_following = User.objects.create_user(
            username="test_user_2")
        self.client_authorized = Client()
        self.client_authorized.force_login(self.user)
        self.text = "test_text"
        self.post = Post.objects.create(
            text=self.text, author=self.user_we_are_following
        )

    def tearDown(self):
        cache.clear()

    def test_follow(self):
        self.client_authorized.get(
            reverse("profile_follow",
                    args=[self.user_we_are_following.username])
        )
        self.assertIsNotNone(Follow.objects.first())

    def test_unfollow(self):
        self.client_authorized.get(
            reverse("profile_unfollow",
                    args=[self.user_we_are_following.username])
        )
        self.assertIsNone(Follow.objects.first())

    def test_index_foolow(self):
        self.client_authorized.get(
            reverse("profile_follow",
                    args=[self.user_we_are_following.username])
        )
        resp = self.client_authorized.get(reverse("follow_index"))
        self.assertContains(resp, self.text)

    def test_index_not_follow(self):
        resp = self.client_authorized.get(reverse("follow_index"))
        self.assertNotContains(resp, self.text)


class TestComments(TestCase):
    def setUp(self):
        self.client_unauthorized = Client()
        self.client_authorized = Client()
        self.user = User.objects.create_user(username="test_user")
        self.client_authorized.force_login(self.user)
        self.post = Post.objects.create(text="test_text", author=self.user)

    def test_authorized_user_commenting(self):
        resp = self.client_authorized.post(
            reverse("add_comment", args=[self.user.username, self.post.pk]),
            {"text": "тест_комментарий"},
            follow=True,
        )
        self.assertContains(resp, "тест_комментарий")

    def test_unauthorized_user_commenting(self):
        resp = self.client_unauthorized.post(
            reverse("add_comment", args=[self.user.username, self.post.pk]),
            {"text": "тест_комментарий"},
            follow=True,
        )
        self.assertNotContains(resp, "тест_комментарий")
