import { forwardRef } from 'react';
import type {InputHTMLAttributes } from 'react';
type TextInputProps = InputHTMLAttributes<HTMLInputElement>;

const TextInput = forwardRef<HTMLInputElement, TextInputProps>(
  ({ className = '', ...props }, ref) => {
    return (
      <input
        ref={ref}
        className={`ml-3 px-3 py-2 rounded border border-white bg-gray-800 text-white placeholder-white focus:outline-none focus:ring-2 focus:ring-white ${className}`}
        {...props}
      />
    );
  }
);

TextInput.displayName = 'TextInput';

export default TextInput;
