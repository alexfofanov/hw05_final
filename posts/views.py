from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, New_postForm
from .models import Comment, Follow, Group, Post, User


def index(request):
    post_list = (
        Post.objects.select_related('author', 'group')
        .order_by('-pub_date')
        .all()
    )
    paginator = Paginator(
        post_list, 10
    )  # показывать по 10 записей на странице.
    page_number = request.GET.get(
        'page'
    )  # переменная в URL с номером запрошенной страницы
    page = paginator.get_page(
        page_number
    )  # получить записи с нужным смещением
    return render(
        request, 'index.html', {'page': page, 'paginator': paginator}
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = (
        Post.objects.select_related('author', 'group')
        .filter(group=group)
        .order_by('-pub_date')
    )
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'group.html',
        {'group': group, 'page': page, 'paginator': paginator},
    )


@login_required
def new_post(request):
    if request.method == 'POST':
        form = New_postForm(request.POST, files=request.FILES or None)
        if form.is_valid():
            Post.objects.create(
                author=request.user,
                group=form.cleaned_data['group'],
                text=form.cleaned_data['text'],
                image=form.cleaned_data['image'],
            )
            return redirect('/')

    form = New_postForm()
    return render(
        request,
        'new_post.html',
        {'form': form, 'title': 'Добавить запись', 'button_name': 'Добавить'},
    )


def profile(request, username):
    author = get_object_or_404(User, username=username)

    folower_count = Follow.objects.filter(author=author).count()
    post_count = Post.objects.filter(author=author).count()
    following_count = Follow.objects.filter(user=author).count()

    post_list = (
        Post.objects.select_related('author', 'group')
        .order_by('-pub_date')
        .filter(author=author)
    )
    paginator = Paginator(
        post_list, 10
    )  # показывать по 10 записей на странице.
    page_number = request.GET.get(
        'page'
    )  # переменная в URL с номером запрошенной страницы
    page = paginator.get_page(
        page_number
    )  # получить записи с нужным смещением

    following_status = False
    if request.user.is_authenticated:
        if Follow.objects.filter(
            user=request.user, author=User.objects.get(username=username)
        ).exists():
            following_status = True

    return render(
        request,
        'profile.html',
        {
            'page': page,
            'paginator': paginator,
            'author': author,
            'post_count': post_count,
            'username': username,
            'following_status': following_status,
            'folower_count': folower_count,
            'following_count': following_count,
        },
    )


def post_view(request, username, post_id):
    author = get_object_or_404(User, username=username)
    posts_count = Post.objects.filter(author=author).count()
    folower_count = Follow.objects.filter(author=author).count()
    following_count = Follow.objects.filter(user=author).count()
    items = Comment.objects.select_related('post', 'author').filter(
        post=post_id
    )

    post = get_object_or_404(Post, id=post_id)
    form = CommentForm()
    return render(
        request,
        'post.html',
        {
            'post': post,
            'author': author,
            'folower_count': folower_count,
            'following_count': following_count,
            'posts_count': posts_count,
            'username': username,
            'form': form,
            'items': items,
        },
    )


@login_required
def post_edit(request, username, post_id):
    if request.user.username == username:
        post = get_object_or_404(Post, id=post_id)
        if request.method == 'POST':
            form = New_postForm(
                request.POST, files=request.FILES or None, instance=post
            )
            if form.is_valid():
                post.group = form.cleaned_data['group']
                post.text = form.cleaned_data['text']
                post.save()
                return redirect(f'/{username}/{post_id}/')
        form = New_postForm(files=request.FILES or None, instance=post)
        return render(
            request,
            'new_post.html',
            {
                'form': form,
                'post': post,
                'title': 'Редактировать запись',
                'button_name': 'Сохранить',
            },
        )
    else:
        return redirect(f'/{username}/{post_id}')


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            return redirect(
                'post', username=post.author.username, post_id=post_id
            )
    form = CommentForm()
    return redirect('post', username=post.author.username, post_id=post_id)


@login_required
def post_delete(request, username, post_id):
    if request.user.username == username:
        post = get_object_or_404(Post, pk=post_id)
        if request.method == 'POST':
            form = New_postForm(request.POST, instance=post)
            post.delete()
            return redirect('/')
        form = New_postForm(instance=post)
        return render(
            request,
            'new_post.html',
            {
                'form': form,
                'title': 'Удалить запись',
                'button_name': 'Удалить',
            },
        )
    else:
        return redirect(f'/{username}/{post_id}')


@login_required
def follow_index(request):
    follow_records = Follow.objects.filter(user=request.user).select_related(
        'author'
    )
    follow_authors = []
    for follow in follow_records:
        follow_authors.append(follow.author)

    post_list = (
        Post.objects.select_related('author', 'group')
        .filter(author__in=follow_authors)
        .order_by('-pub_date')
        .all()
    )
    paginator = Paginator(
        post_list, 10
    )  # показывать по 10 записей на странице.
    page_number = request.GET.get(
        'page'
    )  # переменная в URL с номером запрошенной страницы
    page = paginator.get_page(
        page_number
    )  # получить записи с нужным смещением

    return render(
        request, 'follow.html', {'page': page, 'paginator': paginator}
    )


@login_required
def profile_follow(request, username):
    author = User.objects.get(username=username)
    if (
        request.user != author and not Follow.objects.filter(
            user=request.user, author=author
        ).exists()
    ):
        Follow.objects.create(user=request.user, author=author)

    return redirect('profile', username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()

    return redirect('profile', username)


def page_not_found(request, exception):
    # Переменная exception содержит отладочную информацию,
    # выводить её в шаблон пользователской страницы 404 мы не станем
    return render(request, 'misc/404.html', {'path': request.path}, status=404)


def server_error(request):
    return render(request, 'misc/500.html', status=500)
