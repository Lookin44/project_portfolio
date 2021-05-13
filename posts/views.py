from django.core.paginator import Paginator
from django.shortcuts import redirect, render, get_object_or_404
from .forms import PostForm, CommentForm, GroupForm, UserEditForm
from .models import Group, Post, Comment, Follow, User, Like
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page
from django.http.response import HttpResponseRedirect


@cache_page(1, key_prefix='index_page')
def index(request):
    post_list = Post.objects.annotate_liked(request.user).all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {'page': page,
               'paginator': paginator}
    return render(request, 'index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    group_list = group.posts.annotate_liked(request.user).all()
    paginator = Paginator(group_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {'group': group,
               'page': page,
               'paginator': paginator}
    return render(request, 'group.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.annotate_liked(request.user).all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    following = False
    if request.user.is_authenticated:
        following = request.user.follower.filter(author=author).exists()
    context = {'page': page,
               'paginator': paginator,
               'author': author,
               'following': following}
    return render(request, 'profile.html', context)


@login_required
def profile_edit(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        return redirect('profile', username=author.username)
    form = UserEditForm(request.POST or None, instance=author)
    if form.is_valid():
        form.save()
        return redirect('profile', username=author.username)
    return render(request, 'profile_edit.html', {'form': form})


def post_view(request, username, post_id):
    post = get_object_or_404(
        Post.objects.annotate_liked(request.user),
        id=post_id,
        author__username=username
    )
    form = CommentForm()
    comments = post.comments.filter(post=post).all()
    context = {'post': post,
               'author': post.author,
               'form': form,
               'comments': comments}
    return render(request, 'post.html', context)


@login_required
def new_post(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('index')
    return render(request, 'post_new.html', {'form': form})


@login_required
def new_group(request):
    form = GroupForm(request.POST or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('index')
    return render(request, 'group_new.html', {'form': form})


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    if request.user != post.author:
        return redirect('post', username=username, post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('post',
                        username=post.author,
                        post_id=post_id
                        )
    return render(request, 'post_new.html', {'form': form, 'post': post})


@login_required
def post_delete(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    if request.user == post.author:
        post.delete()
        return redirect('profile', username=username)
    return redirect('post', username=username, post_id=post_id)


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        new_comment = form.save(commit=False)
        new_comment.author = request.user
        new_comment.post = post
        new_comment.save()
    return redirect('post', username=username, post_id=post_id)


@login_required
def delete_comment(request, username, post_id, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    if request.user == comment.author:
        comment.delete()
    return redirect('post', username=username, post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.annotate_liked(request.user).filter(
        author__following__user=request.user
    )
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    context = {'page': page,
               'paginator': paginator}
    return render(request, 'follow.html', context)


@login_required
def profile_follow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    follow_check = Follow.objects.filter(user=user, author=author).exists()
    if not follow_check and author != user:
        Follow.objects.create(user=request.user, author=author)
    return redirect('profile', username=username)


@login_required
def profile_unfollow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    follow_check = Follow.objects.filter(user=user, author=author)
    if follow_check:
        Follow.objects.filter(user=request.user, author=author).exists()
        follow_check.delete()
    return redirect('profile', username=username)


def page_not_found(request, exception):
    return render(
        request,
        'misc/404.html',
        {'path': request.path},
        status=404
    )


@login_required
def add_like(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    Like.objects.get_or_create(post=post, user=request.user)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


@login_required
def delete_like(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    post.likes.filter(user=request.user).delete()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


def server_error(request):
    return render(request, 'misc/500.html', status=500)
