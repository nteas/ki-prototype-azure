import { FontIcon } from '@fluentui/react/lib/Icon';
import styles from './Button.module.css';
import { Button } from 'react-bootstrap';

interface Props {
	children: string;
	icon?: JSX.Element;
}

export default function Component({ children, icon }: Props): JSX.Element {
	return (
		<Button className={styles.button}>
			<span className={styles.label}>{children}</span>

			{icon && <span className={styles.icon}>{icon}</span>}
		</Button>
	);
}

Component.displayName = 'Button';
