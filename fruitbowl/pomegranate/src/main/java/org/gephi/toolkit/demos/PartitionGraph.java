/*
Copyright 2008-2010 Gephi
Authors : Mathieu Bastian <mathieu.bastian@gephi.org> Patrick Lewis
Website : http://www.gephi.org

This file is part of Gephi.

Gephi is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

Gephi is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with Gephi.  If not, see <http://www.gnu.org/licenses/>.

Heavily Modified by Patrick Lewis
 */
package org.gephi.toolkit.demos;

import java.io.File;
import java.io.IOException;
import org.gephi.graph.api.UndirectedGraph;
import org.gephi.graph.api.GraphController;
import org.gephi.graph.api.GraphModel;
import org.gephi.io.importer.api.Container;
import org.gephi.io.importer.api.ImportController;
import org.gephi.io.processor.plugin.DefaultProcessor;
import org.gephi.project.api.ProjectController;
import org.gephi.project.api.Workspace;
import org.gephi.statistics.plugin.Modularity;
import org.openide.util.Lookup;
import org.gephi.datalab.api.datatables.AttributeTableCSVExporter;
import org.gephi.graph.api.Table;


/**
 * This demo shows how to get partitions and export them as csv
 * <p>
 * Partitions are always created from an attribute column, in the data since
 * import or computed from an algorithm. The demo so the following tasks:
 * <ul><li>Import a graph file.</li>
 * <li>Run modularity algorithm, detecting communities. The algorithm create a
 * new column and label nodes with a community number.</li>
 * Partitions are built from the <code>PartitionController</code> service. 
 *
 * @author Mathieu Bastian, Patrick Lewis
 */
public class PartitionGraph {
    
    public File export_file;
    public File import_file;
    
    public PartitionGraph(String in, String out){
        ///create a partition graph
        export_file = new File(out);
        try {
        import_file = new File(in);

        }
        catch (Exception ex){
            ex.printStackTrace();
        }
    }

    public void script() {
        //Init a project - and therefore a workspace
        ProjectController pc = Lookup.getDefault().lookup(ProjectController.class);
        pc.newProject();
        Workspace workspace = pc.getCurrentWorkspace();

        //Get controllers and models
        ImportController importController = Lookup.getDefault().lookup(ImportController.class);
        GraphModel graphModel = Lookup.getDefault().lookup(GraphController.class).getGraphModel();

        //Import file
        Container container = null;
        try {

            container = importController.importFile(this.import_file);
        } catch (Exception ex) {
            System.out.println("Import Broken");
            ex.printStackTrace();
        }
        //Append imported data to GraphAPI
        importController.process(container, new DefaultProcessor(), workspace);
        //See if graph is well imported
        UndirectedGraph graph = graphModel.getUndirectedGraph();
        System.out.println("Nodes: " + graph.getNodeCount());
        System.out.println("Edges: " + graph.getEdgeCount());

        //Run modularity algorithm - community detection
        Modularity modularity = new Modularity();
        modularity.setResolution(1.0);
        modularity.execute(graphModel);
        //Export
        try {
            //AttributeTableCSVExporter atse = new AttributeTableCSVExporter();
            Table t = graphModel.getNodeTable();
            AttributeTableCSVExporter.writeCSVFile(graph, t ,this.export_file);
        } catch (IOException ex) {
            ex.printStackTrace();
            return;
        }
    }
}
