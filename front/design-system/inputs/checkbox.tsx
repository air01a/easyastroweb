import { forwardRef } from 'react';
import type { InputHTMLAttributes } from 'react';

type CheckboxProps = InputHTMLAttributes<HTMLInputElement>;

const Checkbox = forwardRef<HTMLInputElement, CheckboxProps>(
  ({ className = '', ...props }, ref) => {
    return (
      <input
        ref={ref}
        type="checkbox"
        className={`w-4 h-4 accent-white bg-gray-800 border border-white rounded focus:outline-none focus:ring-2 focus:ring-white ${className}`}
        {...props}
      />
    );
  }
);

Checkbox.displayName = 'Checkbox';

export default Checkbox;
