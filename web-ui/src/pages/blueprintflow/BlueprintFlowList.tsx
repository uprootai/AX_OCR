import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import {
  FolderOpen,
  Plus,
  Edit2,
  Trash2,
  Play,
  Copy,
  Clock,
  GitBranch,
  Calendar
} from 'lucide-react';
import { workflowApi, type WorkflowDefinition } from '../../lib/api';
import { useWorkflowStore } from '../../store/workflowStore';

interface SavedWorkflow extends WorkflowDefinition {
  id: string;
  created_at: string;
  updated_at: string;
}

export default function BlueprintFlowList() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [workflows, setWorkflows] = useState<SavedWorkflow[]>([]);
  const [loading, setLoading] = useState(true);
  const { clearWorkflow, loadWorkflow } = useWorkflowStore();

  useEffect(() => {
    loadWorkflows();
  }, []);

  const loadWorkflows = async () => {
    try {
      const list = await workflowApi.listWorkflows();
      setWorkflows(list);
    } catch (error) {
      console.error('Failed to load workflows:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleNewWorkflow = () => {
    clearWorkflow();
    navigate('/blueprintflow/builder');
  };

  const handleEditWorkflow = async (workflow: SavedWorkflow) => {
    try {
      const loadedWorkflow = await workflowApi.loadWorkflow(workflow.id);
      loadWorkflow(loadedWorkflow);
      navigate('/blueprintflow/builder');
    } catch (error) {
      console.error('Failed to load workflow:', error);
      alert('Failed to load workflow');
    }
  };

  const handleDeleteWorkflow = async (id: string, name: string) => {
    if (!confirm(`Delete workflow "${name}"?`)) return;

    try {
      await workflowApi.deleteWorkflow(id);
      await loadWorkflows();
    } catch (error) {
      console.error('Failed to delete workflow:', error);
      alert('Failed to delete workflow');
    }
  };

  const handleDuplicateWorkflow = async (workflow: SavedWorkflow) => {
    try {
      const duplicated = {
        ...workflow,
        name: `${workflow.name} (Copy)`,
      };
      const { id: _id, created_at: _created, updated_at: _updated, ...cleanDuplicated } = duplicated as typeof duplicated & { id?: string; created_at?: string; updated_at?: string };
      const workflowToSave = cleanDuplicated;

      await workflowApi.saveWorkflow(workflowToSave);
      await loadWorkflows();
    } catch (error) {
      console.error('Failed to duplicate workflow:', error);
      alert('Failed to duplicate workflow');
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      <div className="flex items-center justify-between mb-8">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <FolderOpen className="w-8 h-8 text-cyan-600" />
            <h1 className="text-4xl font-bold text-gray-900 dark:text-white">
              {t('blueprintflow.myWorkflows')}
            </h1>
            <Badge className="bg-cyan-600">BETA</Badge>
          </div>
          <p className="text-gray-600 dark:text-gray-400">
            {t('blueprintflow.savedWorkflowsDesc')}
          </p>
        </div>
        <Button
          onClick={handleNewWorkflow}
          className="flex items-center gap-2 px-4 py-2 bg-cyan-600 text-white rounded-lg hover:bg-cyan-700 transition-colors"
        >
          <Plus className="w-5 h-5" />
          {t('blueprintflow.newWorkflow')}
        </Button>
      </div>

      {loading ? (
        <Card>
          <CardContent className="text-center py-12">
            <div className="animate-spin w-8 h-8 border-4 border-cyan-600 border-t-transparent rounded-full mx-auto"></div>
            <p className="mt-4 text-gray-600 dark:text-gray-400">Loading workflows...</p>
          </CardContent>
        </Card>
      ) : workflows.length === 0 ? (
        <Card>
          <CardContent>
            <div className="text-center py-12 text-gray-500 dark:text-gray-400">
              <FolderOpen className="w-16 h-16 mx-auto mb-4 opacity-50" />
              <p className="text-lg font-medium">{t('blueprintflow.noWorkflows')}</p>
              <p className="text-sm mt-2">
                {t('blueprintflow.createFirstWorkflow')}
              </p>
              <Button
                onClick={handleNewWorkflow}
                className="mt-6 flex items-center gap-2 mx-auto"
              >
                <Plus className="w-5 h-5" />
                {t('blueprintflow.newWorkflow')}
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {workflows.map((workflow) => (
            <Card
              key={workflow.id}
              className="hover:shadow-lg transition-shadow cursor-pointer group"
            >
              <CardHeader>
                <div className="flex items-start justify-between">
                  <CardTitle className="flex-1 text-lg font-semibold text-gray-900 dark:text-white">
                    {workflow.name}
                  </CardTitle>
                  <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleEditWorkflow(workflow);
                      }}
                      className="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-blue-600"
                      title="Edit"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDuplicateWorkflow(workflow);
                      }}
                      className="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-green-600"
                      title="Duplicate"
                    >
                      <Copy className="w-4 h-4" />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteWorkflow(workflow.id, workflow.name);
                      }}
                      className="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-red-600"
                      title="Delete"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                {workflow.description && (
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
                    {workflow.description}
                  </p>
                )}
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
                    <div className="flex items-center gap-1">
                      <GitBranch className="w-4 h-4" />
                      <span>{workflow.nodes.length} nodes</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Calendar className="w-4 h-4" />
                      <span>{workflow.edges.length} edges</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-500">
                    <Clock className="w-3 h-3" />
                    <span>Updated {formatDate(workflow.updated_at)}</span>
                  </div>

                  <div className="flex gap-2 pt-3 border-t border-gray-200 dark:border-gray-700">
                    <Button
                      onClick={() => handleEditWorkflow(workflow)}
                      variant="outline"
                      className="flex-1 flex items-center justify-center gap-2 text-sm"
                    >
                      <Edit2 className="w-4 h-4" />
                      Edit
                    </Button>
                    <Button
                      onClick={() => {
                        handleEditWorkflow(workflow);
                        // TODO: Auto-execute on load
                      }}
                      className="flex-1 flex items-center justify-center gap-2 text-sm bg-green-600 hover:bg-green-700"
                    >
                      <Play className="w-4 h-4" />
                      Run
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
