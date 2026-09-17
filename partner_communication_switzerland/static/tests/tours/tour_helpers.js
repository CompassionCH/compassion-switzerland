/**
 * Helpers shared by the onboarding tours.
 */
import { delay } from "@web/core/utils/concurrency";
import { rpc } from "@web/core/network/rpc";
import { serializeDateTime } from "@web/core/l10n/dates";
import { stepUtils } from "@web_tour/tour_service/tour_utils";

const { DateTime } = luxon;

const MAX_QUEUE_PASSES = 10;

export const QUEUE_TIMEOUT = 60000;

/** Calls a method on an Odoo model, as the web client does. */
const callKw = (model, method, args) =>
  rpc("/web/dataset/call_kw", { model, method, args, kwargs: {} });

/**
 * Runs the jobs the server queued, instead of waiting for the cron to pick
 * them up, and fails the tour with the server side error of the ones that did
 * not go through.
 *
 * The steps calling this need {@link QUEUE_TIMEOUT} as their `timeout`.
 *
 * @param {Number} settle milliseconds to wait first, for the jobs that are
 *   queued with an eta in the near future.
 */
export const runQueuedJobs = async (settle = 0) => {
  await delay(settle);
  // The jobs that failed before this call are not ours to report.
  const alreadyFailed = await callKw("queue.job.replacement", "search", [
    [["state", "=", "failed"]],
  ]);

  let due = 0;
  for (let pass = 0; pass < MAX_QUEUE_PASSES; pass++) {
    await callKw("queue.job.replacement", "cron_run_jobs", [[]]);
    due = await callKw("queue.job.replacement", "search_count", [
      [
        ["state", "=", "pending"],
        ["eta", "<=", serializeDateTime(DateTime.now())],
        ["is_predecessor_complete", "=", true],
      ],
    ]);
    if (!due) {
      break;
    }
  }

  // Failures come first: a job left due is usually the successor of one that
  // failed, and its error is the one worth reading.
  const failed = await callKw("queue.job.replacement", "search_read", [
    [
      ["state", "=", "failed"],
      ["id", "not in", alreadyFailed],
    ],
    ["job_function", "job_result"],
  ]);
  if (failed.length) {
    throw new Error(
      "Queued job(s) failed:\n" +
        failed.map((j) => `${j.job_function}: ${j.job_result}`).join("\n"),
    );
  }
  if (due) {
    throw new Error(
      `${due} job(s) were still due after ` +
        `${MAX_QUEUE_PASSES} passes of the queue`,
    );
  }
};

/**
 * Opens an item of a menu section of an app, which is three clicks: the app in
 * the apps menu, then the section in the top bar, then the item it drops down.
 *
 * @param {Object} menu
 * @param {String} menu.app xmlid of the app to open.
 * @param {String} menu.section xmlid of the section of the app.
 * @param {String} menu.item xmlid of the item of the section.
 * @param {String} menu.description what opening the app is for.
 */
export const openMenu = ({ app, section, item, description }) => [
  ...stepUtils.goToAppSteps(app, description),
  {
    content: `Open the ${section} section`,
    trigger: `button[data-menu-xmlid="${section}"]`,
    run: "click",
  },
  {
    content: `Open ${item}`,
    trigger: `.dropdown-item[data-menu-xmlid="${item}"]`,
    run: "click",
  },
];

/** Types a value in the search view of a list and validates it. */
export const searchFor = (value) => [
  {
    content: `Search ${value}`,
    trigger: ".o_searchview_input",
    run: `edit ${value}`,
  },
  {
    content: "Validate the search",
    trigger: ".o_searchview_input",
    run: "press Enter",
  },
];

export const reloadStep = (content) => ({
  content,
  trigger: ".o_form_view",
  run: () => window.location.reload(),
  expectUnloadPage: true,
});
