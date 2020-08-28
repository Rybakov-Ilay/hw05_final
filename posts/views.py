from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User


def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(request,
                  "index.html",
                  {"page": page, "paginator": paginator})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)

    return render(
        request,
        "group.html",
        {"group": group, "page": page, "paginator": paginator}
    )


@login_required
def new_post(request):
    if not request.method == "POST":
        form = PostForm()
        return render(request, "new.html", {"form": form})
    form = PostForm(request.POST, files=request.FILES or None)
    if not form.is_valid():
        return render(request, "new.html", {"form": form})
    post_get = form.save(commit=False)
    post_get.author = request.user
    post_get.save()
    return redirect("index")


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)

    context = {"author": author, "page": page, "paginator": paginator,
               "posts": posts}

    if not request.user.is_anonymous:
        following = Follow.objects.filter(user=request.user,
                                          author=author).exists()
        context["following"] = following

    return render(request, "profile.html", context)


def post_view(request, username, post_id):
    author = get_object_or_404(User, username=username)
    post = author.posts.get(author=author, id=post_id)
    count_post = author.posts.count()
    comments = post.comments.all()
    form = CommentForm()
    return render(
        request,
        "post.html",
        {
            "post": post,
            "author": author,
            "count_post": count_post,
            "comments": comments,
            "form": form,
        },
    )


def post_edit(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    if post.author != request.user:
        return redirect("post", username=post.author, post_id=post.pk)
    form = PostForm(request.POST or None, files=request.FILES or None,
                    instance=post)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect("post", username=post.author, post_id=post.pk)
    return render(
        request, "new.html",
        {"form": form, "post": post, "is_form_edit": True},
    )


def page_not_found(request, exception):
    return render(request, "misc/404.html", {"path": request.path}, status=404)


def server_error(request):
    return render(request, "misc/500.html", status=500)


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id)
    author = get_object_or_404(User, username=username)
    comments = post.comments.all()

    form = CommentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        new_comment = form.save(commit=False)
        new_comment.author = request.user
        new_comment.post = post
        new_comment.save()
        return redirect("post", username=username, post_id=post_id)

    return render(
        request,
        "post.html",
        {"post": post, "author": author, "form": form, "comments": comments},
    )


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(request, "follow.html",
                  {"page": page, "paginator": paginator})


@login_required
def profile_follow(request, username):
    follow_author = get_object_or_404(User, username=username)
    if request.user != follow_author:
        Follow.objects.get_or_create(user=request.user, author=follow_author)
    return redirect("profile", username=username)


@login_required
def profile_unfollow(request, username):
    unfollow_from_author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user).filter(
        author=unfollow_from_author
    ).delete()
    return redirect("profile", username=username)
