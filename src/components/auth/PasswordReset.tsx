import { AlertTriangle, CheckCircle, Loader, Lock } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { toast } from 'react-toastify';
import { z } from 'zod';

import { authService } from '@/api/services/authService';

// Password utility functions
const calculatePasswordStrength = (password: string): number => {
  if (!password) return 0;
  
  let score = 0;
  score += Math.min(password.length * 4, 25);
  
  if (/[A-Z]/.test(password)) score += 10;
  if (/[a-z]/.test(password)) score += 10;
  if (/[0-9]/.test(password)) score += 10;
  if (/[^A-Za-z0-9]/.test(password)) score += 15;
  
  return Math.min(100, score);
};

const getPasswordStrengthLabel = (strength: number): { label: string; color: string } => {
  if (strength < 30) return { label: 'Weak', color: 'text-red-500' };
  if (strength < 60) return { label: 'Moderate', color: 'text-yellow-400' };
  if (strength < 80) return { label: 'Good', color: 'text-green-400' };
  return { label: 'Strong', color: 'text-green-500' };
};

type ApiErrorResponse = {
  response?: {
    data?: any;
  };
};

const formatAuthError = (error: ApiErrorResponse): string => {
  let errorMessage = 'An error occurred. Please try again.';
  const errorData = error.response?.data;
 
  if (errorData) {
    if (typeof errorData === 'string') {
      errorMessage = errorData;
    } else if (errorData.detail) {
      errorMessage = errorData.detail;
    } else if (errorData.non_field_errors) {
      errorMessage = Array.isArray(errorData.non_field_errors)
        ? errorData.non_field_errors.join(', ')
        : errorData.non_field_errors;
    } else if (errorData.error) {
      errorMessage = errorData.error;
    } else {
      const fieldErrors = Object.entries(errorData)
        .filter(([field]) => field !== 'status' && field !== 'code')
        .map(([field, errors]) => {
          if (Array.isArray(errors)) {
            return `${field}: ${errors.join(', ')}`;
          }
          return `${field}: ${errors}`;
        })
        .join('; ');
     
      if (fieldErrors) {
        errorMessage = fieldErrors;
      }
    }
  }
 
  return errorMessage;
};

interface ResetPasswordParams {
  token: string;
  password: string;
  password_confirm: string;
}

const usePasswordReset = () => {
  const requestPasswordReset = useCallback(async (email: string) => {
    try {
      await authService.requestPasswordReset(email);
      return true;
    } catch (error) {
      const errorMessage = formatAuthError(error as ApiErrorResponse);
      toast.error(errorMessage);
      throw error;
    }
  }, []);

  const resetPassword = useCallback(async ({
    token,
    password,
    password_confirm
  }: ResetPasswordParams) => {
    try {
      await authService.resetPassword(token, password, password_confirm);
      return true;
    } catch (error) {
      const errorMessage = formatAuthError(error as ApiErrorResponse);
      toast.error(errorMessage);
      throw error;
    }
  }, []);

  return { requestPasswordReset, resetPassword };
};

const passwordResetSchema = z.object({
  password: z
    .string()
    .min(8, 'Password must be at least 8 characters')
    .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
    .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
    .regex(/[0-9]/, 'Password must contain at least one number')
    .regex(/[^A-Za-z0-9]/, 'Password must contain at least one special character'),
  passwordConfirm: z.string(),
}).refine(data => data.password === data.passwordConfirm, {
  message: "Passwords don't match",
  path: ['passwordConfirm']
});

type PasswordResetFormData = z.infer<typeof passwordResetSchema>;

const RequestResetForm = () => {
  const [email, setEmail] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { requestPasswordReset } = usePasswordReset();

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) {
      setError('Email address is required');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      await requestPasswordReset(email);
      setIsSuccess(true);
    } catch (err: unknown) {
      setError((err as Error).message || 'Failed to request password reset. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  }, [email, requestPasswordReset]);

  if (isSuccess) {
    return (
      <div className="text-center"></div>
        <div className="bg-primary-500/10 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
          <CheckCircle className="w-8 h-8 text-primary-400" />
        </div>
        <h3 className="text-xl font-display font-semibold text-white mb-3">
          Check Your Email
        </h3>
        <p className="text-neutral-400 mb-4">
          We've sent password reset instructions to:
        </p>
        <p className="bg-neutral-800/50 rounded-lg py-2 px-4 mb-6 font-medium text-white">
          {email}
        </p>
        <p className="text-neutral-500 text-sm">
          If you don't receive an email within a few minutes, please check your spam folder or try again.
        </p>
      </div>
    );
  }

  return (
    <div>
      <h3 className="text-xl font-display font-semibold text-white mb-3">
        Reset Your Password
      </h3>
      <p className="text-neutral-400 mb-6">
        Enter your email address and we'll send you instructions to reset your password.
      </p>

      {error && (
        <div className="bg-red-900/50 border border-red-800 rounded-lg px-4 py-3 mb-6 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
          <p className="text-red-300">{error}</p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label htmlFor="email" className="block text-sm font-medium text-neutral-300 mb-1">
            Email Address
          </label>
          <input
            id="email"
            type="email"
            className="w-full bg-neutral-800/50 border border-neutral-700 rounded-lg px-4 py-2 text-white placeholder-neutral-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500/50"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>

        <button
          type="submit"
          className="w-full bg-primary-500 hover:bg-primary-600 text-white px-4 py-2 rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
          disabled={isSubmitting}
        >
          {isSubmitting ? (
            <>
              <Loader className="w-5 h-5 animate-spin" />
              <span>Processing...</span>
            </>
          ) : (
            <span>Send Reset Instructions</span>
          )}
        </button>
      </form>
    </div>
  );
};

interface ResetPasswordFormProps {
  token: string;
}

const ResetPasswordForm = ({ token }: ResetPasswordFormProps) => {
  const navigate = useNavigate();
  const { resetPassword } = usePasswordReset();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [passwordStrength, setPasswordStrength] = useState(0);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors }
  } = useForm<PasswordResetFormData>();

  const password = watch('password', '');
  
  useEffect(() => {
    if (password) {
      setPasswordStrength(calculatePasswordStrength(password));
    }
  }, [password]);

  const onSubmit = useCallback(async (data: PasswordResetFormData) => {
    setIsSubmitting(true);
    setError(null);

    try {
      await resetPassword({
        token,
        password: data.password,
        password_confirm: data.passwordConfirm
      });
      
      setIsSuccess(true);
      
      setTimeout(() => {
        navigate('/signin', { 
          state: { message: 'Your password has been reset successfully. You can now sign in with your new password.' }
        });
      }, 3000);
    } catch (err: unknown) {
      setError((err as Error).message || 'Failed to reset password. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  }, [token, resetPassword, navigate]);

  if (isSuccess) {
    return (
      <div className="text-center">
        <div className="bg-primary-500/10 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
          <CheckCircle className="w-8 h-8 text-primary-400" />
        </div>
        <h3 className="text-xl font-display font-semibold text-white mb-3">
          Password Reset Successful
        </h3>
        <p className="text-neutral-400 mb-4">
          Your password has been reset successfully.
        </p>
        <p className="text-neutral-500">
          You will be redirected to the login page in a moment...
        </p>
      </div>
    );
  }

  return (
    <div>
      <h3 className="text-xl font-display font-semibold text-white mb-3">
        Create New Password
      </h3>
      <p className="text-neutral-400 mb-6">
        Please create a new secure password for your account.
      </p>

      {error && (
        <div className="bg-red-900/50 border border-red-800 rounded-lg px-4 py-3 mb-6 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
          <p className="text-red-300">{error}</p>
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        <div>
          <label htmlFor="password" className="block text-sm font-medium text-neutral-300 mb-1">
            New Password
          </label>
          <div className="relative">
            <input
              id="password"
              type="password"
              className="w-full bg-neutral-800/50 border border-neutral-700 rounded-lg px-4 py-2 text-white placeholder-neutral-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500/50"
              placeholder="••••••••"
              {...register('password')}
            />
            <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
              <Lock className="w-5 h-5 text-neutral-500" />
            </div>
          </div>
          {errors.password && (
            <p className="mt-1 text-sm text-red-400">{errors.password.message}</p>
          )}
          
          {password && (
            <div className="mt-2">
              <div className="h-1 w-full bg-neutral-700 rounded-full">
                <div
                  className={`h-1 rounded-full ${
                    passwordStrength < 30 ? 'bg-red-500' : 
                    passwordStrength < 60 ? 'bg-yellow-500' : 
                    passwordStrength < 80 ? 'bg-green-400' : 'bg-green-500'
                  }`}
                  style={{ width: `${passwordStrength}%` }}
                ></div>
              </div>
              <p className={`text-xs mt-1 ${getPasswordStrengthLabel(passwordStrength).color}`}>
                Password strength: {getPasswordStrengthLabel(passwordStrength).label}
              </p>
            </div>
          )}
        </div>

        <div>
          <label htmlFor="passwordConfirm" className="block text-sm font-medium text-neutral-300 mb-1">
            Confirm Password
          </label>
          <input
            id="passwordConfirm"
            type="password"
            className="w-full bg-neutral-800/50 border border-neutral-700 rounded-lg px-4 py-2 text-white placeholder-neutral-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500/50"
            placeholder="••••••••"
            {...register('passwordConfirm')}
          />
          {errors.passwordConfirm && (
            <p className="mt-1 text-sm text-red-400">{errors.passwordConfirm.message}</p>
          )}
        </div>

        <button
          type="submit"
          className="w-full bg-primary-500 hover:bg-primary-600 text-white px-4 py-2 rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
          disabled={isSubmitting}
        >
          {isSubmitting ? (
            <>
              <Loader className="w-5 h-5 animate-spin" />
              <span>Resetting Password...</span>
            </>
          ) : (
            <span>Reset Password</span>
          )}
        </button>
      </form>
    </div>
  );
};

const PasswordReset = () => {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');

  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center py-12 px-4">
      <div className="bg-neutral-900/50 backdrop-blur-sm rounded-2xl p-8 border border-neutral-800/50 max-w-md w-full">
        {token ? <ResetPasswordForm token={token} /> : <RequestResetForm />}
      </div>
    </div>
  );
};

export default PasswordReset;
