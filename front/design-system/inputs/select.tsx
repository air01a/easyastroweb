import type { SelectHTMLAttributes } from 'react';
import { forwardRef } from 'react';

type SelectInputProps = SelectHTMLAttributes<HTMLSelectElement>;

const SelectInput = forwardRef<HTMLSelectElement, SelectInputProps>(
  ({ className = '', children, ...props }, ref) => {
    return (
      <select
        ref={ref}
        className={`ml-3 mr-3 px-3 py-2 rounded border border-white bg-gray-800 text-white placeholder-white focus:outline-none focus:ring-2 focus:ring-white ${className}`}
        {...props}
      >
        {children}
      </select>
    );
  }
);

SelectInput.displayName = 'SelectInput';

export default SelectInput;
