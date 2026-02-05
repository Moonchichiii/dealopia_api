import { useEffect, useRef, useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { z } from 'zod';
import { useForm } from 'react-hook-form';
import { LogIn, AlertTriangle, Facebook, Github, Loader } from 'lucide-react';
import gsap from 'gsap';

// Form validation schema
const signInSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
  remember: z.boolean().optional(),
});
export type SignInFormData = z.infer<typeof signInSchema>;

interface SignInProps {
  isModal?: boolean;
  onToggleView?: () => void;
  onSuccess?: () => void;
}

const SignIn: React.FC<SignInProps> = ({ isModal = false, onToggleView, onSuccess }) => {
  const formRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const location = useLocation();
  const { login, isAuthenticated, isLoading: isLoginLoading } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // Get the return path from location state or default to dashboard
  const from = (location.state as { from?: string })?.from || '/dashboard';

  // Initialize form with react-hook-form
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting }
  } = useForm<SignInFormData>();

  // Submit handler
  const onSubmit = async (data: SignInFormData) => {
    try {
      setError(null);
      const response = await login({ email: data.email, password: data.password });
      if (isModal && onSuccess) {
        setSuccess(true);
        setTimeout(() => {
          onSuccess();
        }, 1500);
      }
      return response;
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to sign in. Please try again.');
      }
    }
  };

  // Social login handlers
  const handleGoogleLogin = async () => {
    try {
      await login({ provider: 'google' });
      if (isModal && onSuccess) {
        onSuccess();
      }
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to sign in with Google.');
      }
    }
  };

  const handleGithubLogin = async () => {
    try {
      await login({ provider: 'github' });
      if (isModal && onSuccess) {
        onSuccess();
      }
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to sign in with GitHub.');
      }
    }
  };

  // Redirect if already authenticated (for full page version)
  useEffect(() => {
    if (!isModal && isAuthenticated) {
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, navigate, from, isModal]);

  // GSAP animation
  useEffect(() => {
    if (!formRef.current) return;
    const ctx = gsap.context(() => {
      gsap.from('.form-element', {
        y: 20,
        opacity: 0,
        duration: 0.6,
        stagger: 0.1,
        ease: 'power3.out'
      });
    }, formRef);
    return () => ctx.revert();
  }, []);

  // Success message component
  const renderSuccessMessage = () => (
    <div className="text-center p-4">
      <div className="mb-8">
        <div className="mx-auto w-16 h-16 bg-primary-500/20 rounded-full flex items-center justify-center">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h2 className="mt-6 text-3xl font-display font-bold bg-gradient-to-r from-primary-200 via-white to-accent-200 bg-clip-text text-transparent">
          Sign In Successful!
        </h2>
        <p className="mt-2 text-neutral-400">Welcome back to DealOpia.</p>
      </div>
    </div>
  );

  // Main content render function
  const renderContent = () => (
    <>
      <div className="text-center mb-8">
        <h2 className="text-3xl font-display font-bold bg-gradient-to-r from-primary-200 via-white to-accent-200 bg-clip-text text-transparent">
          Welcome Back
        </h2>
        <p className="mt-2 text-neutral-400">Sign in to access your account</p>
      </div>

      <div ref={formRef} className="bg-neutral-900/50 backdrop-blur-sm rounded-2xl p-8 border border-neutral-800/50">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          {error && (
            <div className="bg-red-900/50 border border-red-800 text-white px-4 py-3 rounded-lg form-element flex items-start gap-3">
              <AlertTriangle size={18} />
              {error}
            </div>
          )}

          <div className="form-element">
            <label htmlFor="email" className="block text-sm font-medium text-neutral-300 mb-1">
              Email Address
            </label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              className="w-full bg-neutral-800/50 border border-neutral-700 rounded-lg px-4 py-2 text-white placeholder-neutral-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500/50"
              placeholder="you@example.com"
              {...register('email')}
            />
            {errors.email && (
              <p className="mt-1 text-sm text-red-400">{errors.email.message}</p>
            )}
          </div>

          <div className="form-element">
            <div className="flex items-center justify-between mb-1">
              <label htmlFor="password" className="block text-sm font-medium text-neutral-300">
                Password
              </label>
              <Link to="/forgot-password" className="text-sm text-primary-400 hover:text-primary-300">
                Forgot password?
              </Link>
            </div>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              className="w-full bg-neutral-800/50 border border-neutral-700 rounded-lg px-4 py-2 text-white placeholder-neutral-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500/50"
              placeholder="••••••••"
              {...register('password')}
            />
            {errors.password && (
              <p className="mt-1 text-sm text-red-400">{errors.password.message}</p>
            )}
          </div>

          <div className="flex items-center form-element">
            <input
              id="remember"
              type="checkbox"
              className="h-4 w-4 bg-neutral-800 border-neutral-700 rounded text-primary-500 focus:ring-primary-500/50"
              {...register('remember')}
            />
            <label htmlFor="remember" className="ml-2 block text-sm text-neutral-300">
              Remember me
            </label>
          </div>

          <button
            type="submit"
            disabled={isSubmitting || isLoginLoading}
            className="form-element w-full bg-primary-500 hover:bg-primary-600 text-white px-4 py-2 rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
          >
            {isSubmitting || isLoginLoading ? (
              <>
                <Loader className="animate-spin h-4 w-4" />
                <span>Signing in...</span>
              </>
            ) : (
              <>
                <LogIn size={18} />
                <span>Sign In</span>
              </>
            )}
          </button>
        </form>

        <div className="mt-6">
    <div className="relative form-element">
      <div className="absolute inset-0 flex items-center">
        <div className="w-full border-t border-neutral-700"></div>
      </div>
      <div className="relative flex justify-center text-sm">
        <span className="px-2 bg-neutral-900/50 text-neutral-400">Or sign in with</span>
      </div>
    </div>

    <div className="mt-4 grid grid-cols-2 gap-3 form-element">
      <button
        type="button"
        onClick={handleGoogleLogin}
        className="px-4 py-2 bg-neutral-800/50 hover:bg-neutral-700/70 border border-neutral-700 rounded-lg flex items-center justify-center gap-2 text-neutral-300 transition-colors"
      >
        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 24 24" fill="currentColor">
          <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
          <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
          <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
          <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
        </svg>
        <span>Google</span>
      </button>
      <button
        type="button"
        onClick={handleGithubLogin}
        className="px-4 py-2 bg-neutral-800/50 hover:bg-neutral-700/70 border border-neutral-700 rounded-lg flex items-center justify-center gap-2 text-neutral-300 transition-colors"
      >
        <Github size={20} />
        <span>GitHub</span>
      </button>
    </div>
  </div>

        <div className="mt-6 text-center text-sm text-neutral-400 form-element">
          Don't have an account?{' '}
          {isModal && onToggleView ? (
            <button
              type="button"
              onClick={onToggleView}
              className="text-primary-400 hover:text-primary-300 font-medium"
            >
              Sign up now
            </button>
          ) : (
            <Link to="/signup" className="text-primary-400 hover:text-primary-300 font-medium">
              Sign up now
            </Link>
          )}
        </div>
      </div>
    </>
  );

  if (success) {
    return isModal ? (
      <div className="w-full">{renderSuccessMessage()}</div>
    ) : (
      <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center py-12 px-4">
        <div className="max-w-md w-full text-center">{renderSuccessMessage()}</div>
      </div>
    );
  }

  return isModal ? (
    <div className="w-full p-4">{renderContent()}</div>
  ) : (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center py-12 px-4">
      <div className="max-w-md w-full">{renderContent()}</div>
    </div>
  );
};

export default SignIn;
