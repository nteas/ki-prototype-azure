import styles from './Example.module.css';
import { ChatRegular } from '@fluentui/react-icons';

interface Props {
	text: string;
}

export const Example = ({ text }: Props) => {
	return (
		<div className={styles.example}>
			<p className={styles.exampleText}>{text}</p>
			<ChatRegular
				className={styles.chatIcon}
				aria-hidden="true"
				aria-label="Chat icon"
			/>
		</div>
	);
};
