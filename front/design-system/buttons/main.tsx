import {  forwardRef } from 'react';
import type { ButtonHTMLAttributes } from 'react';

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement>;

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className = '', children, ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={`px-4 py-2 bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed disabled:opacity-70 text-white rounded-md hover:bg-blue-800 focus:outline-none focus:ring-2 focus:ring-blue-500 ${className}`}
        {...props}
      >
        {children}
      </button>
    );
  }
);

Button.displayName = 'Button';

export default Button;
