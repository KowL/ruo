import React, { useEffect } from 'react';
import clsx from 'clsx';
import { createPortal } from 'react-dom';

interface ModalProps {
    isOpen: boolean;
    onClose: () => void;
    title?: string;
    children: React.ReactNode;
    footer?: React.ReactNode;
    className?: string;
}

const Modal: React.FC<ModalProps> = ({
    isOpen,
    onClose,
    title,
    children,
    footer,
    className,
}) => {
    useEffect(() => {
        const handleEsc = (e: KeyboardEvent) => {
            if (e.key === 'Escape') onClose();
        };
        if (isOpen) {
            document.addEventListener('keydown', handleEsc);
            document.body.style.overflow = 'hidden';
        }
        return () => {
            document.removeEventListener('keydown', handleEsc);
            document.body.style.overflow = 'unset';
        };
    }, [isOpen, onClose]);

    if (!isOpen) return null;

    return createPortal(
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-black/50 backdrop-blur-sm transition-opacity"
                onClick={onClose}
            />

            {/* Panel */}
            <div
                className={clsx(
                    "relative w-full max-w-md transform overflow-hidden rounded-2xl bg-[var(--color-surface-1)] p-6 text-left shadow-xl transition-all border border-[var(--color-surface-3)]",
                    className
                )}
            >
                {title && (
                    <h3 className="text-lg font-medium leading-6 text-[var(--color-text-primary)] mb-4">
                        {title}
                    </h3>
                )}

                <div className="mt-2 text-[var(--color-text-secondary)]">
                    {children}
                </div>

                {footer && (
                    <div className="mt-6 flex justify-end gap-3">
                        {footer}
                    </div>
                )}
            </div>
        </div>,
        document.body
    );
};

export default Modal;
