import { Button } from '@fluentui/react-components';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCog } from '@fortawesome/pro-regular-svg-icons';
import { useNavigate } from 'react-router-dom';

import styles from './SettingsButton.module.scss';

interface Props {
	className?: string;
}

export const SettingsButton = ({ className }: Props) => {
	const navigate = useNavigate();

	return (
		<div className={`${styles.container} ${className ?? ''}`}>
			<Button
				icon={<FontAwesomeIcon icon={faCog} />}
				onClick={() => navigate('/admin')}>
				Innstillinger
			</Button>
		</div>
	);
};
