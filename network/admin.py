from django.contrib import admin
from .models import Post, User, Comment


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'content_preview', 'timestamp', 'get_likes_count', 'get_comments_count')
    list_filter = ('timestamp', 'user')
    search_fields = ('content', 'user__username')
    readonly_fields = ('timestamp', 'get_likes_count', 'get_comments_count', 'get_likes_list')
    filter_horizontal = ('likes',)
    
    fieldsets = (
        ('Post Information', {
            'fields': ('user', 'content', 'timestamp')
        }),
        ('Engagement', {
            'fields': ('likes',),
            'description': 'Users who liked this post'
        }),
        ('Statistics', {
            'fields': ('get_likes_count', 'get_comments_count', 'get_likes_list'),
            'classes': ('collapse',)
        }),
    )
    
    def content_preview(self, obj):
        """Show first 50 characters of post content"""
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content Preview'
    
    def get_likes_count(self, obj):
        """Show number of likes"""
        return obj.likes.count()
    get_likes_count.short_description = 'Likes Count'
    
    def get_comments_count(self, obj):
        """Show number of comments"""
        return obj.post_comments.count()
    get_comments_count.short_description = 'Comments Count'
    
    def get_likes_list(self, obj):
        """Show list of users who liked"""
        return ', '.join([user.username for user in obj.likes.all()])
    get_likes_list.short_description = 'Users Who Liked'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'post_preview', 'content_preview', 'timestamp')
    list_filter = ('timestamp', 'user')
    search_fields = ('content', 'user__username', 'post__content')
    readonly_fields = ('timestamp',)
    
    fieldsets = (
        ('Comment Information', {
            'fields': ('post', 'user', 'content', 'timestamp')
        }),
    )
    
    def post_preview(self, obj):
        """Show preview of the post this comment is on"""
        return obj.post.content[:30] + '...' if len(obj.post.content) > 30 else obj.post.content
    post_preview.short_description = 'Post'
    
    def content_preview(self, obj):
        """Show first 50 characters of comment content"""
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Comment'


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'get_followers_count', 'get_following_count', 'total_posts', 'is_active')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('username', 'email')
    filter_horizontal = ('following', 'groups', 'user_permissions')
    
    fieldsets = (
        ('User Information', {
            'fields': ('username', 'email', 'first_name', 'last_name')
        }),
        ('Status', {
            'fields': ('is_active', 'is_staff', 'is_superuser')
        }),
        ('Relationships', {
            'fields': ('following',),
            'description': 'Users this user is following'
        }),
        ('Permissions', {
            'fields': ('groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
    )