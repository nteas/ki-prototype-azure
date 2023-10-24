import styles from './Example.module.css';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCommentLines } from '@fortawesome/pro-regular-svg-icons';

interface Props {
	text: string;
}

export const Example = ({ text }: Props) => {
	return (
		<div className={styles.example}>
			<p className={styles.exampleText}>{text}</p>
			<FontAwesomeIcon
				className={styles.chatIcon}
				aria-hidden="true"
				aria-label="Chat icon"
				icon={faCommentLines}
			/>
		</div>
	);
};
