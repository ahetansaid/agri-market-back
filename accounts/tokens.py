from django.contrib.auth.tokens import PasswordResetTokenGenerator


class TokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        # SECURITE : inclure le hash du mot de passe et last_login (comme le
        # generateur Django par defaut) pour que le token soit invalide des
        # que le mot de passe change ou que l'utilisateur se connecte. Sinon
        # un lien d'activation/reset fuite reste rejouable pendant tout le
        # PASSWORD_RESET_TIMEOUT.
        login_timestamp = (
            ""
            if user.last_login is None
            else user.last_login.replace(microsecond=0, tzinfo=None)
        )
        return (
            str(user.pk)
            + str(user.password)
            + str(login_timestamp)
            + str(timestamp)
            + str(user.is_active)
        )


generate_token = TokenGenerator()


# class TokenGenerator(PasswordResetTokenGenerator):
#     def _make_hash_value(self, user, timestamp):
#         return (
#             six.text_type(user.pk) + six.text_type(timestamp) +
#             six.text_type(user.is_active)
#         )
# account_activation_token = TokenGenerator()


# class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
#     def _make_hash_value(self, user,  timestamp):
#         return (
#             six.text_type(user.pk) + six.text_type(timestamp)
#             #six.text_type(user.is_active)
#         )


# class PasswordResetToken(PasswordResetTokenGenerator):
#     def _make_hash_value(self, user, timestamp):
#         return (
#             six.text_type(user.pk) + six.text_type(timestamp) +
#             six.text_type(user.is_active)
#         )


# #account_activation_token = AccountActivationTokenGenerator()
# password_reset_token = PasswordResetToken()
