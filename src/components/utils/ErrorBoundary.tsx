import { useRouteError, useNavigate } from 'react-router-dom';

const ErrorBoundary = () => {
    const error = useRouteError();
    const navigate = useNavigate();

    const goBack = () => {
        navigate(-1);
    };
    
    return (
        <div className="min-h-screen flex items-center justify-center p-8 bg-secondary-950">
            <div className="bg-white/5 backdrop-blur-md rounded-xl p-8 max-w-lg text-center">
                <div className="w-20 h-20 mx-auto mb-6 flex items-center justify-center rounded-full bg-accent-pink/10 text-accent-pink">
                    <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <circle cx="12" cy="12" r="10"></circle>
                        <line x1="12" y1="8" x2="12" y2="12"></line>
                        <line x1="12" y1="16" x2="12.01" y2="16"></line>
                    </svg>
                </div>
                
                <h2 className="text-2xl font-bold mb-4 text-white">Oops! Something went wrong</h2>
                
                <p className="text-text-secondary mb-6">
                    {error?.message || 'An unexpected error occurred while processing your request.'}
                </p>
                
                <div className="flex justify-center space-x-4">
                    <button 
                        onClick={goBack}
                        className="bg-secondary-800 text-white px-6 py-3 rounded-full font-medium hover:bg-secondary-700 transition-colors"
                    >
                        Previous Page
                    </button>
                    <a 
                        href="/"
                        className="inline-block bg-accent-pink text-white px-6 py-3 rounded-full font-medium hover:bg-accent-pink/90 transition-colors"
                    >
                        Back to Home
                    </a>
                </div>
            </div>
        </div>
    );
};

export default ErrorBoundary;
