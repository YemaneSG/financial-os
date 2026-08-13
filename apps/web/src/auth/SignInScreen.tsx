import { useAuth } from "./AuthProvider";

export function SignInScreen() {
  const { signIn, signInError } = useAuth();

  return (
    <main className="sign-in" aria-label="Sign in">
      <h1 className="sign-in__title">Financial OS</h1>
      <p className="sign-in__privacy">
        Private receipt capture. Your data stays yours.
      </p>

      {signInError && (
        <div role="alert" className="alert alert--error" id="sign-in-error">
          {signInError}
        </div>
      )}

      <button
        type="button"
        className="btn btn--primary btn--large"
        onClick={() => void signIn()}
        aria-describedby={signInError ? "sign-in-error" : undefined}
        aria-label="Continue with Google"
      >
        Continue with Google
      </button>

      <p className="sign-in__note">
        Only the authorized account can sign in. No public registration.
      </p>
    </main>
  );
}
