import styles from './Example.module.css';
import { ChatRegular } from '@fluentui/react-icons';

interface Props {
	text: string;
	value: string;
	onClick: (value: string) => void;
}

export const Example = ({ text, value, onClick }: Props) => {
	return (
		<div className={styles.example} onClick={() => onClick(value)}>
			<p className={styles.exampleText}>{text}</p>
			<ChatRegular
				className={styles.chatIcon}
				aria-hidden="true"
				aria-label="Chat icon"
			/>
		</div>
	);
};
