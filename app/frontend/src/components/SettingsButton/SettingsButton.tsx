import { Settings24Regular } from '@fluentui/react-icons';
import { Button } from '@fluentui/react-components';

import styles from './SettingsButton.module.css';
import { useApp } from '../../pages/layout/Layout';

interface Props {
	className?: string;
	onClick: () => void;
}

export const SettingsButton = ({ className }: Props) => {
	const { panelOpen, setPanelOpen } = useApp();

	return (
		<div className={`${styles.container} ${className ?? ''}`}>
			<Button
				icon={<Settings24Regular />}
				onClick={() => setPanelOpen(!panelOpen)}>
				Innstillinger
			</Button>
		</div>
	);
};
