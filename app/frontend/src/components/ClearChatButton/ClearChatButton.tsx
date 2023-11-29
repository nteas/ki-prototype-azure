import { Button } from '@fluentui/react-components';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faTrash } from '@fortawesome/pro-regular-svg-icons';

import styles from './ClearChatButton.module.scss';

interface Props {
	className?: string;
	onClick: () => void;
	disabled?: boolean;
}

export const ClearChatButton = ({ className, disabled, onClick }: Props) => {
	return (
		<div className={`${styles.container} ${className ?? ''}`}>
			<Button
				icon={<FontAwesomeIcon icon={faTrash} />}
				disabled={disabled}
				onClick={onClick}>
				Tøm chat
			</Button>
		</div>
	);
};
