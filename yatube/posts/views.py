import datetime

from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from .models import Post, Group, User, Follow

from .forms import PostForm, CommentForm


def paginator(request, post_list):
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj


def index(request):
    post_list = Post.objects.all()
    # добавлено, чтобы время публикации постов
    # отображалось в часовом поясе пользователя
    LOCAL_TIMEZONE = datetime.datetime.now(
        datetime.timezone.utc
    ).astimezone().tzinfo
    context = {
        'page_obj': paginator(request, post_list),
        'local_timezone': LOCAL_TIMEZONE,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    LOCAL_TIMEZONE = datetime.datetime.now(
        datetime.timezone.utc
    ).astimezone().tzinfo
    context = {
        'group': group,
        'page_obj': paginator(request, post_list),
        'local_timezone': LOCAL_TIMEZONE,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    LOCAL_TIMEZONE = datetime.datetime.now(
        datetime.timezone.utc
    ).astimezone().tzinfo
    following = Follow.objects.filter(
        user=request.user if request.user.is_authenticated else None,
        author=author
    ).exists()
    context = {
        'author': author,
        'page_obj': paginator(request, author.posts.all()),
        'local_timezone': LOCAL_TIMEZONE,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    current_user = request.user
    form = CommentForm()
    date = timezone.now
    LOCAL_TIMEZONE = datetime.datetime.now(
        datetime.timezone.utc
    ).astimezone().tzinfo
    context = {
        'post': post,
        'current_user': current_user,
        'comments': post.comments.all(),
        'form': form,
        'date': date,
        'local_timezone': LOCAL_TIMEZONE,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    user = request.user
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if form.is_valid():
        new_post = form.save(commit=False)
        new_post.author = user
        new_post.save()
        return redirect('posts:profile', user.username)
    return render(request, 'posts/post_create.html', {'form': form})


def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author.id != request.user.id:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    context = {
        'form': form,
        'post': post,
    }
    return render(request, 'posts/post_create.html', context)


@login_required
def add_comment(request, post_id):
    user = request.user
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id)


@login_required
def follow(request):
    user = request.user
    follows = user.follower.all()
    post_list = Post.objects.none()
    for follow in follows:
        post_list |= follow.author.posts.all()
    LOCAL_TIMEZONE = datetime.datetime.now(
        datetime.timezone.utc
    ).astimezone().tzinfo
    context = {
        'local_timezone': LOCAL_TIMEZONE,
        'page_obj': paginator(request, post_list),
    }
    return render(request, 'posts/followed.html', context)


@login_required
def profile_follow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    if user != author:
        Follow.objects.get_or_create(
            user=user,
            author=author
        )
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(
        user=user,
        author=author,
    ).delete()
    return redirect('posts:profile', username)
