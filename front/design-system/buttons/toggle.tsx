import { forwardRef } from 'react';
import type { ButtonHTMLAttributes } from 'react';

interface ToggleButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  active?: boolean;
}

const ToggleButton = forwardRef<HTMLButtonElement, ToggleButtonProps>(
  ({ className = '', children, active = false, ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={`
          px-3 py-1 rounded-md text-sm font-medium border transition h-11 
          ${active ? 'bg-green-600 text-white border-green-600' : 'bg-white text-gray-700 border-gray-300'}
          ${className}
        `}
        {...props}
      >
        {children}
      </button>
    );
  }
);

ToggleButton.displayName = 'ToggleButton';

export default ToggleButton;
