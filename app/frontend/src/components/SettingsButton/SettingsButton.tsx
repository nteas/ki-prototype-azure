import { Button } from '@fluentui/react-components';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCog } from '@fortawesome/pro-regular-svg-icons';

import styles from './SettingsButton.module.scss';

interface Props {
	className?: string;
	onClick: () => void;
}

export const SettingsButton = ({ className, onClick }: Props) => {
	return (
		<div className={`${styles.container} ${className ?? ''}`}>
			<Button icon={<FontAwesomeIcon icon={faCog} />} onClick={onClick}>
				Innstillinger
			</Button>
		</div>
	);
};
