import { Row, Col } from "antd";
import "./PageHeader.css";

export default ({ title, extra, ...props }) => (
    <Row className="page-header" justify="space-between" {...props}>
        <Col>
            <span className="page-header-title">{title}</span>
        </Col>
        <Col>{extra}</Col>
    </Row>
);
