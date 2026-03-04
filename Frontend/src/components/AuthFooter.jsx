import { Link } from 'react-router-dom';
import { MdHelp, MdVerified, MdGppMaybe, MdCreditCard } from 'react-icons/md';

/**
 * AuthFooter — shared dynamic footer for all auth pages (Login, Signup, OTPVerify, ForgotPassword, Onboarding).
 * Pass `showBadges={false}` to hide the SSL/Licensed/PCI badges (useful if the parent shows them elsewhere).
 */
const AuthFooter = ({ showBadges = true }) => {
  const year = new Date().getFullYear();

  return (
    <div className="mt-10 pt-6 border-t border-slate-100 space-y-5" style={{ fontFamily: 'Manrope, sans-serif' }}>
      {showBadges && (
        <div className="flex flex-wrap justify-center gap-5">
          {[
            { icon: <MdVerified size={20} />, label: 'SSL Secure' },
            { icon: <MdGppMaybe size={20} />, label: 'Licensed Bank' },
            { icon: <MdCreditCard size={20} />, label: 'PCI Compliant' },
          ].map(({ icon, label }) => (
            <div key={label} className="flex items-center gap-2 text-slate-400 hover:text-slate-600 transition-all cursor-default">
              {icon}
              <span className="text-xs font-bold uppercase tracking-wider">{label}</span>
            </div>
          ))}
        </div>
      )}

      <div className="flex flex-wrap justify-between items-center gap-3">
        <button type="button"
          className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-semibold transition-colors"
          style={{ background: 'rgba(74,134,232,0.1)', color: '#4a86e8' }}
        >
          <MdHelp size={17} /> Help Center
        </button>

        <div className="flex gap-4 text-xs text-slate-400">
          <Link to="#" className="hover:text-blue-600 transition-colors">Privacy Policy</Link>
          <Link to="#" className="hover:text-blue-600 transition-colors">Terms of Service</Link>
        </div>
      </div>

      <p className="text-center text-xs text-slate-300">
        © {year} Sentinel Bank Corp. All rights reserved.
      </p>
    </div>
  );
};

export default AuthFooter;
