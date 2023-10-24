import styles from './Button.module.css';
import { Button } from 'react-bootstrap';

interface Props {
	children: string;
	className?: string;
	icon?: JSX.Element;
	onClick?: () => void;
	type?: 'button' | 'submit' | 'reset';
}

export default function Component({
	children,
	className,
	icon,
	onClick,
	type = 'submit',
}: Props): JSX.Element {
	return (
		<Button
			className={`${styles.button} ${className}`}
			onClick={onClick}
			type={type}>
			<span className={styles.label}>{children}</span>

			{icon && <span className={styles.icon}>{icon}</span>}
		</Button>
	);
}

Component.displayName = 'Button';
