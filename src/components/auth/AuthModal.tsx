import { createPortal } from 'react-dom';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { X } from 'lucide-react';
import SignIn from '@/components/auth/SignIn';
import SignUp from '@/components/auth/SignUp';

interface AuthModalProps {
    isOpen: boolean;
    onClose: () => void;
    initialView?: 'signIn' | 'signUp';
}

const AuthModal: React.FC<AuthModalProps> = ({
    isOpen,
    onClose,
    initialView = 'signIn'
}) => {
    const [view, setView] = useState<'signIn' | 'signUp'>(initialView);
    
    const toggleView = useCallback(() => {
        setView(view === 'signIn' ? 'signUp' : 'signIn');
    }, [view]);
    
    const handleSuccess = useCallback(() => {
        onClose();
    }, [onClose]);
    
    useEffect(() => {
        setView(initialView);
    }, [initialView]);
    
    useEffect(() => {
        if (!isOpen) return;
        
        const handleEscape = (e: KeyboardEvent) => {
            if (e.key === 'Escape') onClose();
        };
        
        document.addEventListener('keydown', handleEscape);
        document.body.style.overflow = 'hidden';
        
        return () => {
            document.removeEventListener('keydown', handleEscape);
            document.body.style.overflow = '';
        };
    }, [isOpen, onClose]);
    
    if (!isOpen) return null;
    
    return createPortal(
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div 
                className="absolute inset-0 bg-black/80 backdrop-blur-sm"
                onClick={onClose}
            />
            
            <div className="relative z-10 w-full max-w-md">
                <div className="bg-neutral-900/90 backdrop-blur-md rounded-2xl overflow-hidden">
                    <button
                        className="absolute top-4 right-4 p-1 rounded-full bg-neutral-800/50 text-neutral-400 hover:bg-neutral-700/70 hover:text-white transition-colors"
                        onClick={onClose}
                    >
                        <X size={20} />
                    </button>
                    
                    <div className="pt-10">
                        {view === 'signIn' ? (
                            <SignIn 
                                isModal
                                onToggleView={toggleView}
                                onSuccess={handleSuccess}
                            />
                        ) : (
                            <SignUp 
                                isModal
                                onToggleView={toggleView}
                                onSuccess={handleSuccess}
                            />
                        )}
                    </div>
                </div>
            </div>
        </div>,
        document.getElementById('modal-root') || document.body
    );
};

export const useAuthModal = () => {
    const [isOpen, setIsOpen] = useState(false);
    const [initialView, setInitialView] = useState<'signIn' | 'signUp'>('signIn');
    
    const openSignIn = useCallback(() => {
        setInitialView('signIn');
        setIsOpen(true);
    }, []);
    
    const openSignUp = useCallback(() => {
        setInitialView('signUp');
        setIsOpen(true);
    }, []);
    
    const closeModal = useCallback(() => {
        setIsOpen(false);
    }, []);
    
    const authModalElement = useMemo(() => (
        <AuthModal 
            isOpen={isOpen}
            onClose={closeModal}
            initialView={initialView}
        />
    ), [isOpen, closeModal, initialView]);
    
    return {
        isOpen,
        initialView,
        openSignIn,
        openSignUp,
        closeModal,
        AuthModal: authModalElement
    };
};

export default AuthModal;
