import { useEffect, useRef } from 'react';
const CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID;
export default function GoogleSignIn({ onCredential, onError }) {
  const buttonRef = useRef(null);
  const credentialRef = useRef(onCredential);
  const errorRef = useRef(onError);
  useEffect(() => { credentialRef.current = onCredential; }, [onCredential]);
  useEffect(() => { errorRef.current = onError; }, [onError]);
  useEffect(() => {
    if (!CLIENT_ID || CLIENT_ID.startsWith('YOUR_')) return;
    const render = () => {
      if (!window.google?.accounts?.id || !buttonRef.current) return;
      if (window.__equityLensGoogleClientId !== CLIENT_ID) {
        window.google.accounts.id.initialize({ client_id: CLIENT_ID, callback: (response) => credentialRef.current(response.credential), auto_select: false });
        window.__equityLensGoogleClientId = CLIENT_ID;
      }
      buttonRef.current.replaceChildren();
      window.google.accounts.id.renderButton(buttonRef.current, { theme: 'filled_black', size: 'large', shape: 'pill', text: 'continue_with', width: 320 });
    };
    if (window.google?.accounts?.id) render();
    else {
      let script = document.getElementById('equitylens-google-script');
      if (!script) {
        script = document.createElement('script');
        script.id = 'equitylens-google-script';
        script.src = 'https://accounts.google.com/gsi/client';
        script.async = true;
        script.defer = true;
        script.onerror = () => errorRef.current?.('Unable to load Google Sign-In.');
        document.head.appendChild(script);
      }
      script.addEventListener('load', render, { once: true });
    }
  }, []);
  if (!CLIENT_ID || CLIENT_ID.startsWith('YOUR_')) return <div className="google-unconfigured">Google Sign-In setup required · Add VITE_GOOGLE_CLIENT_ID to frontend/.env</div>;
  return <div className="google-wrap"><div ref={buttonRef} /></div>;
}
