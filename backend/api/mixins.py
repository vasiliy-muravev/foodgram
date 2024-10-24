class CurrentRecipeMixin:

    def get_current_recipe(self, obj, model) -> bool:
        request = self.context.get('request')
        if request is None:
            return False
        user = request.user
        if user.is_anonymous:
            return False
        return model.objects.filter(
            user=user,
            recipe=obj
        ).exists()
