from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    following = models.ManyToManyField('self', symmetrical=False, related_name='followers', blank=True)
    
    def __str__(self):
        return self.username
    
    def get_following_count(self):
        """Return the number of users this user follows."""
        return self.following.count()
    
    def get_followers_count(self):
        """Return the number of users following this user."""
        return self.followers.count()

    def total_posts(self):
        """Return the number of posts this user has."""
        return self.posts.count()

    def get_total_likes(self):
        """Return the number of likes this user has."""
        return self.liked_posts.count()

class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    content = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(User, related_name="liked_posts", blank=True)

    def get_likes_count(self):
        """Return the number of likes on this post."""
        return self.likes.count()
    
    def get_comments_count(self):
        """Return the number of comments on this post."""
        return self.post_comments.count()

    def __str__(self):
        return f"{self.user} - {self.content}"


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="post_comments")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user.username} commented on {self.post.user.username}'s post"