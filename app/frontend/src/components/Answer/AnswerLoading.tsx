import { Stack } from '@fluentui/react';
import { animated, useSpring } from '@react-spring/web';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faStars } from '@fortawesome/pro-solid-svg-icons';

import styles from './Answer.module.scss';

export const AnswerLoading = () => {
	const animatedStyles = useSpring({
		from: { opacity: 0 },
		to: { opacity: 1 },
	});

	return (
		<animated.div style={{ ...animatedStyles }}>
			<Stack
				className={styles.answerContainer}
				verticalAlign="space-between">
				<FontAwesomeIcon icon={faStars} />

				<Stack.Item grow>
					<p className={styles.answerText}>
						Genererer svar
						<span className={styles.loadingdots} />
					</p>
				</Stack.Item>
			</Stack>
		</animated.div>
	);
};
