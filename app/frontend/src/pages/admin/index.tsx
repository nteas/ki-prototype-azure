import Form from 'react-bootstrap/Form';
import InputGroup from 'react-bootstrap/InputGroup';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faMagnifyingGlass } from '@fortawesome/pro-regular-svg-icons';
import { faCloudArrowUp } from '@fortawesome/pro-solid-svg-icons';

import Layout from '../../components/Layout/Layout';
import Button from '../../components/Button/Button';

import styles from './Admin.module.css';
export function Component(): JSX.Element {
	return (
		<Layout logoSuffix="ADMIN" className={styles.layout}>
			<div className={styles.container}>
				<div className={styles.header}>
					<span>Informasjonskilder</span>

					<Button icon={<FontAwesomeIcon icon={faCloudArrowUp} />}>
						Legg til kilde
					</Button>
				</div>

				<div className={styles.filters}>
					<InputGroup className={styles.search}>
						<Form.Control placeholder="Søk etter kilde" />
						<InputGroup.Text>
							<FontAwesomeIcon icon={faMagnifyingGlass} />
						</InputGroup.Text>
					</InputGroup>

					<Form.Check
						className={styles.check}
						type="checkbox"
						label="Vis kun flagget"
					/>

					<Form.Check
						className={styles.check}
						type="switch"
						label="Vis PDF-kilder"
						defaultChecked={true}
					/>

					<Form.Check
						className={styles.check}
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
