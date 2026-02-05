import { useEffect, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { z } from 'zod';
import { useForm } from 'react-hook-form';
import { UserPlus, Github, Facebook } from 'lucide-react';
import gsap from 'gsap';
import { useRegister, useUser } from '@/hooks/useAuth';

// Form validation schema (used for type inference)

const signUpSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
  first_name: z.string().min(2, 'First name is required'),
  last_name: z.string().min(2, 'Last name is required'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
  password_confirm: z.string(),
  phone_number: z.string().optional(),  
}).refine(data => data.password === data.password_confirm, {
  message: "Passwords don't match",
  path: ['password_confirm'],
});

export type SignUpFormData = z.infer<typeof signUpSchema>;

interface SignUpProps {
  isModal?: boolean;
  onToggleView?: () => void;
  onSuccess?: () => void;
}

const SignUp: React.FC<SignUpProps> = ({ isModal = false, onToggleView, onSuccess }) => {
  const formRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const { register: registerUser, isLoading: isRegisterLoading, error: registerError } = useRegister();
  const { data: user } = useUser();
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  
  const isAuthenticated = !!user;
  
  const { 
    register,
    handleSubmit,
    formState: { errors, isSubmitting }
  } = useForm<SignUpFormData>();

  useEffect(() => {
    if (registerError) {
      setSubmitError(registerError.toString());
    }
  }, [registerError]);

  const onSubmit = async (data: SignUpFormData) => {
    try {
      setSubmitError(null);
      // Exclude 'terms' from the data sent to API
      const { terms, ...registerData } = data;
      const response = await registerUser(registerData);
      setSuccess(true);
      if (isModal && onSuccess) {
        setTimeout(() => {
          onSuccess();
        }, 3000); // Auto close after 3 seconds in modal mode
      }
      return response;
    } catch (err: unknown) {
      if (err instanceof Error) {
        setSubmitError(err.message);
      } else {
        setSubmitError('Failed to sign up. Please try again.');
      }
    }
  };

  const handleGoogleLogin = async () => {
    try {
      await registerUser({ provider: 'google' });
      if (isModal && onSuccess) {
        onSuccess();
      }
    } catch (err: unknown) {
      if (err instanceof Error) {
        setSubmitError(err.message);
      } else {
        setSubmitError('Failed to sign up with Google.');
      }
    }
  };

 
  const handleGithubLogin = async () => {
    try {
      await registerUser({ provider: 'github' });
      if (isModal && onSuccess) {
        onSuccess();
      }
    } catch (err: unknown) {
      if (err instanceof Error) {
        setSubmitError(err.message);
      } else {
        setSubmitError('Failed to sign up with GitHub.');
      }
    }
  };

  // Redirect if already authenticated (for full page usage)
  useEffect(() => {
    if (!isModal && isAuthenticated) {
      navigate('/dashboard');
    }
  }, [isAuthenticated, navigate, isModal]);

  // GSAP animation for form elements
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

  const renderSuccessMessage = () => (
    <div className="text-center p-4">
      <div className="mb-8">
        <div className="mx-auto w-16 h-16 bg-primary-500/20 rounded-full flex items-center justify-center">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h2 className="mt-6 text-3xl font-display font-bold bg-gradient-to-r from-primary-200 via-white to-accent-200 bg-clip-text text-transparent">
          Registration Successful!
        </h2>
        <p className="mt-2 text-neutral-400">
          We've sent a verification email to your inbox. Please check your email and follow the instructions to complete your registration.
        </p>
      </div>
      {isModal && onToggleView ? (
        <button 
          onClick={onToggleView}
          className="inline-flex items-center justify-center px-5 py-3 border border-transparent text-base font-medium rounded-md text-white bg-primary-500 hover:bg-primary-600 shadow-lg shadow-primary-500/20"
        >
          Go to Sign In
        </button>
      ) : (
        <Link 
          to="/signin" 
          className="inline-flex items-center justify-center px-5 py-3 border border-transparent text-base font-medium rounded-md text-white bg-primary-500 hover:bg-primary-600 shadow-lg shadow-primary-500/20"
        >
          Go to Sign In
        </Link>
      )}
    </div>
  );

  const renderForm = () => (
    <>
      <div className="text-center mb-8">
        <h2 className="text-3xl font-display font-bold bg-gradient-to-r from-primary-200 via-white to-accent-200 bg-clip-text text-transparent">
          Create Account
        </h2>
        <p className="mt-2 text-neutral-400">
          Join our community of conscious shoppers
        </p>
      </div>

      <div ref={formRef} className="bg-neutral-900/50 backdrop-blur-sm rounded-2xl p-8 border border-neutral-800/50">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {submitError && (
            <div className="bg-red-900/50 border border-red-800 text-white px-4 py-3 rounded-lg form-element">
              {submitError}
            </div>
          )}
          
          <div className="grid grid-cols-2 gap-4">
            <div className="form-element">
              <label htmlFor="first_name" className="block text-sm font-medium text-neutral-300 mb-1">
                First Name
              </label>
              <input 
                id="first_name"
                type="text"
                className="w-full bg-neutral-800/50 border border-neutral-700 rounded-lg px-4 py-2 text-white placeholder-neutral-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500/50"
                {...register('first_name')}
              />
              {errors.first_name && (
                <p className="mt-1 text-sm text-red-400">{errors.first_name.message}</p>
              )}
            </div>

            <div className="form-element">
              <label htmlFor="last_name" className="block text-sm font-medium text-neutral-300 mb-1">
                Last Name
              </label>
              <input 
                id="last_name"
                type="text"
                className="w-full bg-neutral-800/50 border border-neutral-700 rounded-lg px-4 py-2 text-white placeholder-neutral-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500/50"
                {...register('last_name')}
              />
              {errors.last_name && (
                <p className="mt-1 text-sm text-red-400">{errors.last_name.message}</p>
              )}
            </div>
          </div>

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
            <label htmlFor="phone_number" className="block text-sm font-medium text-neutral-300 mb-1">
              Phone Number (Optional)
            </label>
            <input 
              id="phone_number"
              type="tel"
              className="w-full bg-neutral-800/50 border border-neutral-700 rounded-lg px-4 py-2 text-white placeholder-neutral-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500/50"
              placeholder="+1234567890"
              {...register('phone_number')}
            />
          </div>

          <div className="form-element">
            <label htmlFor="password" className="block text-sm font-medium text-neutral-300 mb-1">
              Password
            </label>
            <input 
              id="password"
              type="password"
              className="w-full bg-neutral-800/50 border border-neutral-700 rounded-lg px-4 py-2 text-white placeholder-neutral-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500/50"
              placeholder="••••••••"
              {...register('password')}
            />
            {errors.password && (
              <p className="mt-1 text-sm text-red-400">{errors.password.message}</p>
            )}
          </div>

          <div className="form-element">
            <label htmlFor="password_confirm" className="block text-sm font-medium text-neutral-300 mb-1">
              Confirm Password
            </label>
            <input 
              id="password_confirm"
              type="password"
              className="w-full bg-neutral-800/50 border border-neutral-700 rounded-lg px-4 py-2 text-white placeholder-neutral-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500/50"
              placeholder="••••••••"
              {...register('password_confirm')}
            />
            {errors.password_confirm && (
              <p className="mt-1 text-sm text-red-400">{errors.password_confirm.message}</p>
            )}
          </div>

          <div className="flex items-start form-element">
            <div className="flex items-center h-5">
              <input
                id="terms"
                type="checkbox"
                className="h-4 w-4 bg-neutral-800 border-neutral-700 rounded text-primary-500 focus:ring-primary-500/50"
                {...register('terms')}
              />
            </div>
            <div className="ml-3 text-sm">
              <label htmlFor="terms" className="text-neutral-300">
                I agree to the <Link to="/terms" className="text-primary-400 hover:text-primary-300">Terms of Service</Link> and <Link to="/privacy" className="text-primary-400 hover:text-primary-300">Privacy Policy</Link>
              </label>
              {errors.terms && (
                <p className="mt-1 text-sm text-red-400">{errors.terms.message}</p>
              )}
            </div>
          </div>

          <button
            type="submit"
            disabled={isSubmitting || isRegisterLoading}
            className="form-element w-full bg-primary-500 hover:bg-primary-600 text-white px-4 py-2 rounded-lg font-medium transition-colors flex items-center justify-center gap-2 mt-6 shadow-lg shadow-primary-500/20"
          >
            {isSubmitting || isRegisterLoading ? (
              <>
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span>Creating Account...</span>
              </>
            ) : (
              <>
                <UserPlus size={18} />
                <span>Sign Up</span>
              </>
            )}
          </button>
        </form>

        <div className="mt-6">
  <div className="relative">
    <div className="absolute inset-0 flex items-center">
      <div className="w-full border-t border-neutral-700"></div>
    </div>
    <div className="relative flex justify-center text-sm">
      <span className="px-2 bg-neutral-900/50 text-neutral-400">Or sign up with</span>
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
          Already have an account?{' '}
          {isModal && onToggleView ? (
            <button 
              type="button" 
              onClick={onToggleView} 
              className="text-primary-400 hover:text-primary-300 font-medium"
            >
              Sign in
            </button>
          ) : (
            <Link to="/signin" className="text-primary-400 hover:text-primary-300 font-medium">
              Sign in
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
    <div className="w-full p-4">{renderForm()}</div>
  ) : (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center py-12 px-4">
      <div className="max-w-md w-full">{renderForm()}</div>
    </div>
  );
};

export default SignUp;