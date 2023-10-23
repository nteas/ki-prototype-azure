import { CloudArrowUp24Filled, Search24Regular } from '@fluentui/react-icons';
import Form from 'react-bootstrap/Form';
import InputGroup from 'react-bootstrap/InputGroup';

import Layout from '../../components/Layout/Layout';
import Button from '../../components/Button/Button';

import styles from './Admin.module.css';
export function Component(): JSX.Element {
	return (
		<Layout logoSuffix="ADMIN" className={styles.layout}>
			<div className={styles.container}>
				<div className={styles.header}>
					<span>Informasjonskilder</span>

					<Button icon={<CloudArrowUp24Filled />}>
						Legg til kilde
					</Button>
				</div>

				<div className={styles.filters}>
					<InputGroup>
						<Form.Control placeholder="Søk etter kilde" />
						<InputGroup.Text>
							<Search24Regular />
						</InputGroup.Text>
					</InputGroup>

					<Form.Check type="checkbox" label="Vis kun flagget" />

					<Form.Check
						type="switch"
						label="Vis PDF-kilder"
						defaultChecked={true}
					/>

					<Form.Check
						type="switch"
						label="Vis web-kilder"
						defaultChecked={true}
					/>
				</div>
			</div>
		</Layout>
	);
}

Component.displayName = 'AdminPage';
