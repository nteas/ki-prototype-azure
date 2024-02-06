import React, { useState } from 'react';
import { Button, Form, InputGroup } from 'react-bootstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faXmark } from '@fortawesome/pro-regular-svg-icons';

interface URLFieldProps {
	defaultValue?: string[];
	name: string;
}

const URLField: React.FC<URLFieldProps> = ({ defaultValue, name }) => {
	const [urls, setUrls] = useState<string[]>(defaultValue || []);

	const addUrlField = () => {
		setUrls([...urls, '']);
	};

	const handleUrlChange = (
		e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
		index: number
	) => {
		const newUrls = [...urls];
		newUrls[index] = e.target.value;
		setUrls(newUrls);
	};

	// remove index from urls
	const removeUrlField = (index: number) => {
		const newUrls = [...urls];
		newUrls.splice(index, 1);
		setUrls(newUrls);
	};

	return (
		<Form.Group>
			<Form.Label>URL</Form.Label>

			{urls?.map((url, index) => (
				<InputGroup key={index} style={{ marginBottom: '20px' }}>
					<Form.Control
						type="url"
						value={url}
						onChange={e => handleUrlChange(e, index)}
					/>

					{url.length > 10 && (
						<Button
							variant="outline-primary"
							type="button"
							onClick={() => {
								window.open(url, '_blank');
							}}>
							Se kilde
						</Button>
					)}

					<Button
						variant="outline-secondary"
						id="button-addon2"
						onClick={() => removeUrlField(index)}>
						<FontAwesomeIcon icon={faXmark} />
					</Button>
				</InputGroup>
			))}

			<div style={{ textAlign: 'right', marginTop: '20px' }}>
				<Button onClick={addUrlField}>Legg til url</Button>
			</div>

			<input type="hidden" name={name} value={JSON.stringify(urls)} />
		</Form.Group>
	);
};

export default URLField;
