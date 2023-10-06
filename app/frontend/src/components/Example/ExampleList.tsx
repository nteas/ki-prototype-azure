import { Example } from './Example';

import styles from './Example.module.css';

export type ExampleModel = {
	text: string;
	value: string;
};

const EXAMPLES: ExampleModel[] = [
	{
		text: 'Hvor mye koster HBO Max?',
		value: 'Hvor mye koster HBO Max?',
	},
	{
		text: 'Hvorfor får jeg svart skjerm når jeg prøver å se på HBO Max?',
		value: 'Hvorfor får jeg svart skjerm når jeg prøver å se på HBO Max?',
	},
	{
		text: 'Hvordan får jeg tilgang til TV 2 Play?',
		value: 'Hvordan får jeg tilgang til TV 2 Play?',
	},
];

interface Props {
	onExampleClicked: (value: string) => void;
}

export const ExampleList = ({ onExampleClicked }: Props) => {
	return (
		<ul className={styles.examplesNavList}>
			{EXAMPLES.map((x, i) => (
				<li key={i} className={styles.examplesListItem}>
					<Example
						text={x.text}
						value={x.value}
						onClick={onExampleClicked}
					/>
				</li>
			))}
		</ul>
	);
};
