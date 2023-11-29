import styles from './Button.module.scss';
import { Button } from 'react-bootstrap';

interface Props {
	children: string;
	className?: string;
	variant?: string;
	icon?: JSX.Element;
	onClick?: () => void;
	type?: 'button' | 'submit' | 'reset';
}

export default function Component({
	children,
	className,
	variant,
	icon,
	onClick,
	type = 'submit',
}: Props): JSX.Element {
	return (
		<Button
			className={`${styles.button} ${className}`}
			onClick={onClick}
			variant={variant}
			type={type}>
			<span className={styles.label}>{children}</span>

			{icon && <span className={styles.icon}>{icon}</span>}
		</Button>
	);
}

Component.displayName = 'Button';
