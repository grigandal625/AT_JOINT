import { CheckOutlined, CloseOutlined, QuestionOutlined } from "@ant-design/icons";
import { Empty, Skeleton, Typography, Divider, Card, Table, Tag } from "antd";
import { Timeline, createTimelineTheme } from "react-svg-timeline";
import { v4 as uuidv4 } from "uuid";

const TimelineHolder = ({ tacts }) => {
    if (!tacts) {
        return <Empty description="Ожидание начала совместного функционирования" />;
    }

    const theme = createTimelineTheme({
        event: { markFillColor: "#003180", markHeight: 15 },
    });
    const dateFormat = (ms) => `${ms}`;
    const lastTact = Math.max(...tacts.map((tact) => tact.tact));

    const lanes = tacts.reduce((accumulator, tact) => {
        tact.opened_intervals.forEach((interval) => {
            const lane = accumulator.find((l) => l.laneId === interval.interval);
            if (!lane) {
                accumulator.push({
                    laneId: interval.interval,
                    label: `Интервал ${interval.interval}`,
                });
            }
        });
        tact.events.forEach((event) => {
            const lane = accumulator.find((l) => l.laneId === event.event);
            if (!lane) {
                accumulator.push({
                    laneId: event.event,
                    label: `Событие ${event.event}`,
                });
            }
        });
        return accumulator;
    }, []);

    const events = tacts.reduce((accumulator, tact) => {
        tact.opened_intervals.forEach((interval) => {
            accumulator.push({
                laneId: interval.interval,
                eventId: uuidv4(),
                tooltip: interval.interval,
                startTimeMillis: interval.open_tact,
                endTimeMillis:
                    interval.close_tact !== null && interval.close_tact !== undefined ? interval.close_tact : lastTact,
            });
        });
        tact.events.forEach((event) => {
            accumulator.push({
                laneId: event.event,
                eventId: uuidv4(),
                tooltip: event.event,
                startTimeMillis: event.occurance_tact,
            });
        });
        return accumulator;
    }, []);

    return (
        <div style={{ width: "100%", overflowX: "scroll" }}>
            <Timeline
                theme={theme}
                dateFormat={dateFormat}
                width={1250}
                height={lanes.length * 40}
                lanes={lanes}
                events={events}
            />
        </div>
    );
};

const SignifiedAllen = ({ signified_meta }) => {
    const dataSource = Object.entries(signified_meta).map(([key, value]) => value);
    return (
        <Table
            style={{ width: "100%" }}
            size="small"
            columns={[
                {
                    dataIndex: "rule",
                    title: "Правило",
                },
                {
                    dataIndex: "allen_operation",
                    title: "Отношение",
                },
                {
                    dataIndex: "value",
                    title: "Значение",
                    render: (value) =>
                        value === undefined || value === null ? (
                            <Tag icon={<QuestionOutlined />}>Не означено</Tag>
                        ) : value ? (
                            <Tag icon={<CheckOutlined />} color="green">
                                Да
                            </Tag>
                        ) : (
                            <Tag icon={<CloseOutlined />} color="red">
                                Нет
                            </Tag>
                        ),
                },
            ]}
            dataSource={dataSource}
            pagination={false}
        />
    );
};

const ATTemporalSolver = ({ atTemporalSolver, inferenceNow }) => {
    return !atTemporalSolver ? (
        !inferenceNow ? (
            <Empty description="Ожидание начала совместного функционирования" />
        ) : (
            <Skeleton active />
        )
    ) : (
        <>
            <Typography.Title level={3}>Интерпретация модели развития событий</Typography.Title>
            <TimelineHolder tacts={atTemporalSolver?.timeline?.tacts} />
            <Divider />
            <Card title="Означенные темпоральные отношения в условиях правил">
                <SignifiedAllen signified_meta={atTemporalSolver?.signified_meta} />
            </Card>
        </>
    );
};

export default ATTemporalSolver;
