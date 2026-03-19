# Bio Metrics

This is a web app to track metrics about oneself like one's blood glucose, weight, blood pressure, food intake, etc. This webapp should be easily usable on a computer as well as a mobile phone. Its main purpose is to help users log some user-defined metric along with its timestamp and then track that metric's movement over time. There are four main user scenarios.

1. User should be able to see a snapshot of all their defined metrics on a dashboard.
2. Upon clicking on any metric snapshot on the dashboard, user should be able analyze the timeseries of that particular metric in greater detail.
3. When on the metric detail page, user should be able to log a new entry for the metric.
4. While on the dashboard, user should be able to define a new metric that want to track going forawrd.

A metric is defined as follows:

* **Name:** The name of the metric.
* **Value Type:** The type of measurement that will be logged for this metric. The values can be of the following three types:
  * **None:** There is no value logged in this type of metric, only the timestamp and other details are captured.
  * **Numeric:** User will log a real number when logging an entry for the metric.
  * **Categorical:** User will log one of several pre-defined categories as this metric's measurement.
* **Unit:** The unit of the metric. This only applies to numeric metrics. 
* **Categories:** The categories that user defines for this metric. When logging user will choose one of these categories. This only applies to categorical metrics.
* **Dimensions:** A metric may zero or many dimensions. Each dimension will be defined in terms of the following:
  * **Name:** Name of the dimension.
  * **Categories:** Values that this dimension can take.

A metric log is defined as follows:

* **Metric:** The metric this logs belongs to.
* **Timestamp:** When the log was recorded.
* **Value:** If this metric was defined as having a value, its numeric or categorical value. The categorical value will be from the categories that have been defined for this metric.
* **Dimension:**  For each defined dimension the following is part of the log:
  * **Name:** Name of the dimension. This will correspond to the name defined as part of the metric definition.
  * **Value:** The value for this dimension. This will be chosen from one of the pre-defined value for this dimension.

The main way of filtering and aggregating the logs is based on the timeseries. The duration of the logs that they are viewing will determine the resampling frequency of the timestamps.

| Duration | Resampling |
| -------- | ---------- |
| 1 day    | Hour       |
| 1 week   | Day        |
| 1 month  | Week       |
| 6 months | Month      |
| 1 Year   | Month      |

In additional to the timeseries, users can also filter and group logs by various dimensions; and in case of categorical metrics, by their values. In any case, user will not be able to filter their logs by value.

In general they can aggregate the values using three functions - `count`, `sum`, and `mean`. But not all functions will apply to all value types. Here is chart that explains which aggregate function can be used with what types of metrics.

| Value Type  | Count | Sum  | Mean |
| ----------- | ----- | ---- | ---- |
| None        | Yes   | No   | No   |
| Numeric     | No    | Yes  | Yes  |
| Categorical | Yes   | No   | No   |

## Examples

This section has some example metrics that illustrate the concepts of the metric definition and metric logs described above. Here is a table of the example metrics:

| Metric Name   | Value Type  | Has Dimensions? |
| ------------- | ----------- | --------------- |
| Meditation    | None        | No              |
| Food          | None        | Yes             |
| Mood          | Categorical | No              |
| Weight        | Numerical   | No              |
| Blood Glucose | Numerical   | Yes             |

### Meditaiton

User wants to log whenever they meditate so they can track the trend of how many times they meditate over time.

#### Definition

* **Name:** Meditation
* **Value Type:** None

#### Logs

| recorded_at |
| ----------- |
| 1767619980  |
| 1769852880  |
| 1770687180  |

#### Filtering

This metric cannot be filtered.

#### Grouping

Only the default timeseries grouping is possible. `count` is the only aggregate function that can be used. Here is what it would look like -

**Weekly Meditation Count**

| Week   | Count |
| ------ | ----- |
| week 1 | 3     |
| week 2 | 4     |

### Food

User wants to be mindful of what they eat. To that end they want to track the kind of meals they have, whether it is healthy or not, how tasty is it, wheather it filled them up or not, whether they cooked it at home, got it from a restaurant, or from a tiffin service.

#### Definition

* **Name:** Food
* **Value Type**: None
* **Dimensions:**
  * *Name:* Source
    * *Categories:* `Home-Cooked`, `Take-Out`, `Tiffin`
  * *Name:* Taste
    * *Categories:* `Delicious`, `Edible`, `Bad`
  * *Name:* Is_Filling
    * *Categories:* `True`, `False`
  * *Name:* Healthy
    * *Categories:* `Very`, `Medium`, `No`

#### Logs

| recorded_on | source      | taste     | is_filling | healthy |
| ----------- | ----------- | --------- | ---------- | ------- |
| 1767486480  | home-cooked | delicious | True       | very    |
| 1767996960  | tiffin      | edible    | True       | medium  |
| 1769852880  | home-cooked | bad       | False      | very    |

#### Filtering

The metric can be filtered by any dimension/value, e.g., I can filter for all home cooked food that was tasty.

#### Grouping

The metric can be grouped by any dimension. Continuing the filtering example, I can group all home cooked food that was tasty by how healthy it was. Here is what it would look like -

**Weekly Count of source == "home-cooked" && taste == "delicious" Food grouped by Healthy** 

| Week   | Healthy                  | Count           |
| ------ | ------------------------ | --------------- |
| week 1 | very<br />medium<br />no | 3<br />4<br />1 |
| week 2 | very<br />medium<br />no | 5<br />2<br />0 |

### Mood

User wants to track their mood throughout the day - whether they are "Happy", "Sad", "Angry", or "Serene".

#### Definition

* **Name:** Mood
* **Value Type:** Categorical
  * **Categories**: One of `Happy`, `Sad`, `Angry`, or `Serene`

#### Logs

| recorded_at | value  |
| ----------- | ------ |
| 1767996960  | Happy  |
| 1769872140  | Happy  |
| 1770732360  | Serene |
| 1770784620  | Sad    |
| 1771975380  | Happy  |

#### Filtering

This metric cannot be filtered.

#### Grouping

Timeseries is the first level of grouping, within that they can be grouped by their values. Only `count` aggregate function can be used, e.g., 

**Weekly Mood Count**

| Week   | Value                      | Count           |
| ------ | -------------------------- | --------------- |
| week 1 | Happy<br />Sad<br />Serene | 2<br />3<br />4 |
| week 2 | Happy<br />Angry<br />Sad  | 3<br />1<br />2 |

### Weight

User wants to monitor their weight over time. They measure their weight in lbs.

#### Definition

* **Name:** Weight
* **Value Type:** Numeric
* **Units:** lbs

#### Logs

| recorded_at | value |
| ----------- | ----- |
| 1767486480  | 180   |
| 1767996960  | 190   |
| 1770784620  | 183   |

#### Filtering

This metric cannot be filtered.

#### Grouping

Only default timeseries grouping is possbile. `sum` and `mean` can be used as the aggregate function. Here is what it can look like -

**Average Weekly Weight**

| Week   | Average |
| ------ | ------- |
| week 1 | 180.2   |
| week 2 | 192.4   |

### Blood Glucose

User wants to track their blood glucose. They usually measure their blood glucose when they are fasting, one hour after breakfast, two hours after breakfast, or after a workout. At times they may also measure it on an ad-hoc basis.

#### Definition

* **Name:** Blood-Glucose
* **Value Type:** Numeric
* **Unit:** mg/dL
* **Dimensions:**
  * *Name:* Event
    * *Categories:* `Fasting`, `Breakfast`, `Workout`, `Ad-Hoc`
  * *Name:* Delta
    * *Categories:* `One-Hour-After`, `Two-Hours-After`

#### Logs

| recorded_on | event     | delta           | value |
| ----------- | --------- | --------------- | ----- |
| 1767619980  | fasting   |                 | 101   |
| 1767996960  | breakfast | one-hour-after  | 150   |
| 1769852880  | breakfast | two-hours-after | 120   |

#### Filtering

The metric can be filtered by any dimension/value, e.g., I can filter for readings that I took one hour after any event, so the filter is `delta == "one-hour-after"`.

#### Grouping

Can group by any dimension. Given the value is a real number, the aggregate function can be configured.  Grouping all breakfast meals by the delta will look like this -

**Weekly Average of event == "breakfast" Blood-Glucose by Delta**

| Week   | Delta                                           | Average               |
| ------ | ----------------------------------------------- | --------------------- |
| week 1 | before<br />one-hour-after<br />two-hours-after | 120<br />150<br />130 |
| week 2 | before<br />one-hour-after<br />two-hours-after | 120<br />150<br />130 |

## User Authentication

User should be able to authenticate themselves to the system using firebase authentication system. For now, just support Google sign in. User should be able to sign out of the system easily and have their data preserved for when they sign in next. User should be able to use different browsers and devices to access their metrics.





















