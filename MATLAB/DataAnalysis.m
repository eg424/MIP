%% Section 1. Free vd Fixed Control Inputs (One Cycle)
t1 = 0.3;
t2 = 0.3;
t3 = 0.2;
t4 = 0.2;

t_free  = [0, t1, t1, t1+t2, t1+t2, t1+t2+t3];
t_fixed = [0, t1, t1, t1+t2, t1+t2, t1+t2+t3, t1+t2+t3, t1+t2+t3+t4];

% Free module
Bx_free      = [1.5, 1.5, 0, 0, 0, 0];
By_free      = [0, 0, 1.5, 1.5, 0, 0];
nablaB_free  = [0, 0, 0, 0, 0, 0];

% Fixed module
Bx_fixed      = [0, 0, 1.5, 1.5, 0, 0, 0, 0];
By_fixed      = [1.5, 1.5, 0, 0, 1.5, 1.5, 0, 0];
nablaB_fixed  = [0, 0, 0, 0, 0.094380952, 0.094380952, 0, 0];

figure('Position', [100, 100, 1000, 600]);

labels = {'|Bx| (mT)', '|By| (mT)', '|∇B| (mT/mm)'};
data_free  = {Bx_free, By_free, nablaB_free};
data_fixed = {Bx_fixed, By_fixed, nablaB_fixed};

for i = 1:3
    % Free
    subplot(3, 2, 2*i - 1);
    stairs(t_free, data_free{i}, 'LineWidth', 2);
    ylabel(labels{i}, 'FontSize', 18);
    if i == 1
        title('Free Module: One Cycle', 'FontSize', 22);
    end
    if i == 3
        xlabel('Time (s)', 'FontSize', 18);
    end
    set(gca, 'FontSize', 18);
    ylim([-0.2, 2]);
    xticks(0:0.2:1.0);
    grid on;
    hold on;
    area([t1+t2 t1+t2+t3], [2 2], ...
        'FaceColor', [0.9 0.9 0.9], ...
        'EdgeColor', 'none', ...
        'ShowBaseLine', 'off');
    uistack(findobj(gca,'Type','area'),'bottom')

    % Fixed
    subplot(3, 2, 2*i);
    stairs(t_fixed, data_fixed{i}, 'LineWidth', 2);
    ylabel(labels{i}, 'FontSize', 18);
    if i == 1
        title('Fixed Module: One Cycle', 'FontSize', 22);
    end
    if i == 3
        xlabel('Time (s)', 'FontSize', 18);
    end
    set(gca, 'FontSize', 18);
    ylim([-0.2, 2]);
    xticks(0:0.2:1.0);
    grid on;
    hold on;
    area([t1+t2+t3 t1+t2+t3+t4], [2 2], ...
        'FaceColor', [0.9 0.9 0.9], ...
        'EdgeColor', 'none', ...
        'ShowBaseLine', 'off');
    uistack(findobj(gca,'Type','area'),'bottom')
end


%% Section 2. Free vs Fixed Trials using H vs H+M

base_path = 'C:\Users\erikg\MIP\MATLAB\Trials';
conditions = {'FixedH', 'FixedHM', 'FreeH', 'FreeHM'};
directions = {'Up','Down','Left','Right'};

% Mappings
module_map = containers.Map(conditions, {'Fixed', 'Fixed', 'Free', 'Free'});
field_map  = containers.Map(conditions, {'Helmholtz', 'HelmholtzMaxwell', 'Helmholtz', 'HelmholtzMaxwell'});

% Conversion factor
pixels_per_mm = 271 / 32;
mm_conversion = @(px) px / pixels_per_mm;

% Initialise data storage
displacement_types = {'Euclidean', 'Manhattan', 'X', 'Y'};
data = struct();
for d = 1:length(displacement_types)
    dtype = displacement_types{d};
    for c = conditions
        data.(dtype).(c{1}) = [];
    end
end

% Read and process each condition + direction
for i = 1:length(conditions)
    condition = conditions{i};
    module = module_map(condition);
    field  = field_map(condition);

    for d = 1:length(directions)
        dir_name = directions{d};
        folder_path = fullfile(base_path, condition, dir_name);
        
        clear dir
        files = dir(fullfile(folder_path, '*.csv'));
        if isempty(files), continue; end

        for f = 1:length(files)
            filepath = fullfile(folder_path, files(f).name);
            T = readtable(filepath);

            % Get final cycle (cycle 10)
            row = T(T.cycle == 10, :);
            if isempty(row), continue; end

            % Store values directly under condition (collapse directions)
            data.Euclidean.(condition)(end+1) = mm_conversion(row.euclidean_from_start);
            data.Manhattan.(condition)(end+1) = mm_conversion(row.manhattan_from_start);
            data.X.(condition)(end+1) = mm_conversion(abs(row.x_disp_from_start));
            data.Y.(condition)(end+1) = mm_conversion(abs(row.y_disp_from_start));
        end
    end
end

% Increase in displacement for fixed module (H vs H+M)
fprintf('\nDisplacements of Fixed Module:\n');

for i = 1:length(displacement_types)
    dtype = displacement_types{i};

    vals_H  = data.(dtype).FixedH;
    vals_HM = data.(dtype).FixedHM;

    if ~isempty(vals_H) && ~isempty(vals_HM)
        mean_H  = mean(vals_H);
        mean_HM = mean(vals_HM);

        abs_inc = mean_HM - mean_H;
        rel_inc = (abs_inc / mean_H) * 100;

        fprintf('%-10s: Mean H = %6.3f mm, Mean HM = %6.3f mm, Increase = %+6.3f mm (%+.1f%%)\n', ...
            dtype, mean_H, mean_HM, abs_inc, rel_inc);
    end
end


% Plotting
bar_labels = {'FixedH', 'FixedHM', 'FreeH', 'FreeHM'};
bar_colors = [0.27 0.51 0.71; 1.0 0.55 0.0; 0.53 0.81 0.92; 0.85 0.65 0.13];

x = 1:length(displacement_types);
bar_width = 0.18;
offsets = [-1.5, -0.5, 0.5, 1.5] * bar_width;

figure('Position', [100, 100, 1200, 500]); hold on;

% Store bar positions and heights for significance annotation
bar_positions = zeros(length(displacement_types),4);
bar_heights   = zeros(length(displacement_types),4);

% Store handles for legend
legend_handles = gobjects(1,4);

for i = 1:length(displacement_types)
    dtype = displacement_types{i};

    means = zeros(1,4);
    sems  = zeros(1,4);
    group_data = cell(1,4);

    for j = 1:4
        vals = data.(dtype).(conditions{j});
        group_data{j} = vals(:);
        means(j) = mean(vals,'omitnan');
        sems(j)  = std(vals,'omitnan')/sqrt(numel(vals));
    end

    % Plot bars + error bars
    for j = 1:4
        x_pos = x(i) + offsets(j);
        bar_positions(i,j) = x_pos;
        bar_heights(i,j)   = means(j);

        if i == 1
            % Capture bar handle for legend
            h = bar(x_pos, means(j), bar_width, 'FaceColor', bar_colors(j,:));
            legend_handles(j) = h; 
        else
            bar(x_pos, means(j), bar_width, 'FaceColor', bar_colors(j,:), ...
                'HandleVisibility','off');
        end

        errorbar(x_pos, means(j), sems(j), 'k', 'LineWidth',1, ...
                 'CapSize',6, 'HandleVisibility','off');
    end


% Statistics (Euclidean & Manhattan)
if ismember(dtype, {'Euclidean','Manhattan'})
    all_vals = vertcat(group_data{:});
    group_ids = arrayfun(@(j) repmat(j, numel(group_data{j}), 1), ...
                         1:4, 'UniformOutput',false);
    group_ids = vertcat(group_ids{:});
    
    [~, ~, stats] = anova1(all_vals, group_ids, 'off'); % suppress plot
    results = multcompare(stats, 'Display','off');      % Tukey HSD

    % Add significance brackets for significant comparisons
    y_max = max(means+sems) * 1.2;
    step = 0.08 * max(means+sems);
    sig_level = 0;

    fprintf('\nTukey HSD comparisons for %s displacement:\n', dtype);
    fprintf('%10s vs %10s | p-value\n', 'Group1', 'Group2');

    for r = 1:size(results,1)
        g1 = results(r,1); g2 = results(r,2); pval = results(r,6);

        % Print p-value
        fprintf('%10s vs %10s | %.5f\n', bar_labels{g1}, bar_labels{g2}, pval);

        if pval < 0.05
            sig_level = sig_level + 1;
            y = y_max + (sig_level-1)*step;
            add_sig_bracket(bar_positions(i,g1), bar_positions(i,g2), y, pval);
        end
    end
end

end

ylabel('Displacement (mm)', 'FontSize', 14);
title('Average Single-Module Displacement After 10 Cycles of Motion in Cardinal Directions', 'FontSize', 14);
xticks(x);
xticklabels(displacement_types);
ax = gca;
ax.XAxis.FontSize = 14;
legend(legend_handles, bar_labels, 'Location','best');
grid on; box on;
hold off;

% Helper for significance brackets
function add_sig_bracket(x1, x2, y, pval)
    if pval < 0.001
        stars = '***';
    elseif pval < 0.01
        stars = '**';
    elseif pval < 0.05
        stars = '*';
    end
    line([x1 x1 x2 x2], [y y+0.02*y y+0.02*y y], ...
        'Color','k','LineWidth',1.2);
    text(mean([x1 x2]), y+0.05*y, stars, ...
        'HorizontalAlignment','center','FontSize',12,'FontWeight','bold');
end

%% Section 3. Chain Self-Assembly: Initial separation distance vs time to assembly
% Initial distances and time to assembly for 2 modules
dist_2 = [8.0, 10.5, 13.0, 15.2, 18.3, 20.8];
time_2 = [0.7, 1.5, 3.2, 4.7, 6.8, NaN];

% Initial distances and time to assembly for 3 modules
distances_3 = [
% m1_m2, m1_m3, m2_m3
    7.0, 6.7, 5.2;
    8.2, 7.3, 6.4;
    11.7, 11.0, 10.3;
    14.2, 12.8, 13.7;
    18.0, 19.2, 19.3;
    20.5, 21.0, 22.5
];
time_3 = [1.8, 2.6, 3.8, 5.6, 8.1, NaN];

% Initial distances and time to assembly for 4 modules
distances_4 = [
% m1_m2, m1_m3, m1_m4, m2_m3, m2_m4, m3_m4
    3.8, 4.2, 3.9, 4.5, 4.1, 4.6;
    5.9, 6.4, 5.8, 6.1, 6.5, 6.2;
    8.7, 10.3, 9.6, 9.1, 10.4, 9.8;
    12.6, 14.0, 13.5, 14.2, 13.0, 14.4;
    19.1, 17.8, 18.9, 18.7, 19.3, 19.4;
    21.7, 22.1, 20.9, 21.5, 22.3, 21.2
];
time_4 = [2.4, 6.6, 9.2, 11.8, 16.5, NaN];

% Mean distances for 3/4 modules
mean_dist_3 = mean(distances_3, 2);
mean_dist_4 = mean(distances_4, 2);

% Figure 1: Assembly Time vs Average Distance
figure;
hold on
plot(dist_2, time_2, 'o-', 'DisplayName', '2 Modules')
plot(mean_dist_3, time_3, 's-', 'DisplayName', '3 Modules')
plot(mean_dist_4, time_4, 'd-', 'DisplayName', '4 Modules')

% Mark failures with red 'x'
scatter(dist_2(isnan(time_2)), zeros(sum(isnan(time_2)),1), 100, 'rx', 'DisplayName', 'Failed Assembly')
scatter(mean_dist_3(isnan(time_3)), zeros(sum(isnan(time_3)),1), 100, 'rx', 'HandleVisibility','off')
scatter(mean_dist_4(isnan(time_4)), zeros(sum(isnan(time_4)),1), 100, 'rx', 'HandleVisibility','off')

xlabel('Average Initial Separation Distance (mm)')
ylabel('Time to Assembly (s)')
title('Self-Assembly into Chain: Time vs Average Initial Distance')
legend('Location', 'best')
grid on
hold off

% Figure 2: Violin plot grouped by number of modules
figure;

dist_violin = [dist_2, distances_3(:)', distances_4(:)'];
modules = [repmat(2, 1, length(dist_2)), repmat(3, 1, numel(distances_3)), repmat(4, 1, numel(distances_4))];
unique_modules = unique(modules);

v = violinplot(modules, dist_violin);
hold on

% Plot means and medians of pairwise distances
for i = 1:length(unique_modules)
    idx = modules == unique_modules(i);
    mean_val = mean(dist_violin(idx));
    median_val = median(dist_violin(idx));
    
    % Plot mean as dashed line
    plot([unique_modules(i)-0.2, unique_modules(i)+0.2], [mean_val, mean_val], ...
        'k--', 'LineWidth', 2, 'DisplayName', 'Mean');

    % Plot median as solid line
    plot([unique_modules(i)-0.2, unique_modules(i)+0.2], [median_val, median_val], ...
        'Color', [0.5 0.5 0.5], 'LineWidth', 1.5, 'DisplayName', 'Median');
end

% Mean distance + assembly time per trial
mean_dist_trials = {dist_2, mean_dist_3, mean_dist_4};
time_trials = {time_2, time_3, time_4};

% Plot time to assembly data
cmap = parula;
all_times = [time_2, time_3, time_4];
time_min = min(all_times(~isnan(all_times)));
time_max = max(all_times(~isnan(all_times)));

for g = 1:numel(unique_modules)
    x = unique_modules(g);
    dists = mean_dist_trials{g};
    times = time_trials{g};
    for j = 1:numel(dists)
        if ~isnan(times(j))
            % Normalise for colormap
            t_norm = (times(j) - time_min) / (time_max - time_min);
            col_idx = max(1, round(t_norm*(size(cmap,1)-1)) + 1);
            scatter(x, dists(j), 80, cmap(col_idx,:), ...
                'filled', 'MarkerEdgeColor','k')
        else
            % Failed trials
            scatter(x, dists(j), 100, 'rx', 'LineWidth', 2)
        end
    end
end

% Colorbar for assembly time
clim([time_min time_max])
ylabel(colorbar, 'Assembly Time (s)')

xlabel('Number of Modules')
ylabel('Pairwise Initial Separation Distance (mm)')
title('Self-Assembly into Chain: Time vs Average Initial Distance')
h_mean   = plot(NaN, NaN, 'k--', 'LineWidth', 1.5, 'DisplayName', 'Mean');
h_median = plot(NaN, NaN, '-', 'Color', [0.5 0.5 0.5], 'LineWidth', 2, 'DisplayName', 'Median');
h_failed = scatter(NaN, NaN, 100, 'rx', 'LineWidth', 2, 'DisplayName', 'Failed Trial');

legend([h_mean, h_median, h_failed], 'Location', 'best')
grid on
hold off

%% Section 4. Reconfiguration Gripper vs Square
filename = 'Reconfiguration.xlsx';
T_gr = readtable(filename, 'Sheet', 'Gripper');
T_sq  = readtable(filename, 'Sheet', 'Square');

% Extract only successful reconfiguration times
times_gr = T_gr.('Var2');
times_gr = times_gr(~isnan(times_gr) & T_gr.('Var3') == 1);

times_sq = T_sq.('Var2');
times_sq = times_sq(~isnan(times_sq) & T_sq.('Var3') == 1);

% Statistics
mean_gr = mean(times_gr);
sem_gr  = std(times_gr)/sqrt(18);

mean_sq = mean(times_sq);
sem_sq  = std(times_sq)/sqrt(14);

% Plot figure
figure;
bar(1:2, [mean_gr, mean_sq], 0.5, 'FaceColor', [0.27 0.51 0.71]);
hold on
errorbar(1:2, [mean_gr, mean_sq], [sem_gr, sem_sq], 'k.', 'LineWidth', 1.5);
set(gca, 'XTick', 1:2, 'XTickLabel', {'Gripper','Square'});
ylabel('Average Reconfiguration Time (s)');
title('Gripper vs Square Reconfiguration Times');
grid on
hold off