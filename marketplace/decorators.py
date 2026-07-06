from django.contrib.auth.decorators import user_passes_test


def validator_required(stage):
    def check_validator(user):
        if not user.is_authenticated:
            return False
        group_name = f"announcement_{stage}_validators"
        return user.groups.filter(name=group_name).exists()

    return user_passes_test(check_validator, login_url="/accounts/login/")
